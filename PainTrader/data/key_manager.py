import json
import os
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import aiohttp
import asyncio

from core.logger import get_logger
from core.secure_storage import secure_storage
from core.config import config

METADATA_FILE = os.path.join(os.path.dirname(__file__), "key_metadata.json")

class KeyManager:
    """
    Manages API keys with metadata and secure storage.
    Handles up to 10 keys, active key selection, and expiration alerts.
    """
    def __init__(self):
        self.logger = get_logger("KeyManager")
        self.metadata = self._load_metadata()
        self._validation_cache = {} # Cache for runtime validation status {uuid: bool}

    def _load_metadata(self) -> Dict:
        if os.path.exists(METADATA_FILE):
            try:
                with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load metadata: {e}")
        return {"keys": [], "active_key_uuid": None, "expiry_alert_days": 7, "auto_login_enabled": False}

    def _save_metadata(self):
        try:
            with open(METADATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save metadata: {e}")

    async def verify_key(self, app_key: str, secret_key: str, is_mock: bool) -> bool:
        """
        Verify key by attempting to get a token from Kiwoom API.
        """
        base_url = "https://mockapi.kiwoom.com" if is_mock else "https://api.kiwoom.com"
        url = f"{base_url}/oauth2/token"
        headers = {"Content-Type": "application/json;charset=UTF-8"}
        data = {
            "grant_type": "client_credentials",
            "appkey": app_key,
            "secretkey": secret_key
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("token") or result.get("access_token"):
                            return True
                        else:
                            self.logger.warning(f"Verification failed: {result}")
                    else:
                        self.logger.warning(f"Verification HTTP Error: {response.status}")
        except Exception as e:
            self.logger.error(f"Verification Exception: {e}")
        return False

    async def probe_key_info(self, app_key: str, secret_key: str) -> Dict:
        """
        Probe key to determine Type (Mock/Real) and Expiry.
        Returns dict with 'valid', 'type', 'expiry_date', 'account_no' (if fetchable).
        """
        result = {"valid": False, "type": None, "expiry_date": None, "account_no": ""}
        
        # Try Real Server first
        real_url = "https://api.kiwoom.com/oauth2/token"
        mock_url = "https://mockapi.kiwoom.com/oauth2/token"
        
        headers = {"Content-Type": "application/json;charset=UTF-8"}
        data = {
            "grant_type": "client_credentials",
            "appkey": app_key,
            "secretkey": secret_key
        }
        
        async with aiohttp.ClientSession() as session:
            # 1. Try Real
            try:
                async with session.post(real_url, headers=headers, json=data) as resp:
                    if resp.status == 200:
                        json_resp = await resp.json()
                        if json_resp.get("access_token") or json_resp.get("token"):
                            result["valid"] = True
                            result["type"] = "REAL"
                            raw_expiry = str(json_resp.get("expires_dt", ""))
                            # Handle YYYYMMDDHHMMSS or YYYY-MM-DD HH:MM:SS
                            if " " in raw_expiry:
                                result["expiry_date"] = raw_expiry.split(" ")[0]
                            elif len(raw_expiry) == 14: # YYYYMMDDHHMMSS
                                result["expiry_date"] = f"{raw_expiry[:4]}-{raw_expiry[4:6]}-{raw_expiry[6:8]}"
                            elif len(raw_expiry) == 8: # YYYYMMDD
                                result["expiry_date"] = f"{raw_expiry[:4]}-{raw_expiry[4:6]}-{raw_expiry[6:8]}"
                            else:
                                # Fallback or unknown format
                                self.logger.warning(f"Unknown expiry format: {raw_expiry}")
                                result["expiry_date"] = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
                            return result
                    else:
                        self.logger.debug(f"Probe Real HTTP {resp.status}")
            except Exception as e:
                self.logger.debug(f"Probe Real failed: {e}")

            # 2. Try Mock
            try:
                async with session.post(mock_url, headers=headers, json=data) as resp:
                    if resp.status == 200:
                        json_resp = await resp.json()
                        if json_resp.get("access_token") or json_resp.get("token"):
                            result["valid"] = True
                            result["type"] = "MOCK"
                            raw_expiry = str(json_resp.get("expires_dt", ""))
                            if " " in raw_expiry:
                                result["expiry_date"] = raw_expiry.split(" ")[0]
                            elif len(raw_expiry) == 14: # YYYYMMDDHHMMSS
                                result["expiry_date"] = f"{raw_expiry[:4]}-{raw_expiry[4:6]}-{raw_expiry[6:8]}"
                            elif len(raw_expiry) == 8: # YYYYMMDD
                                result["expiry_date"] = f"{raw_expiry[:4]}-{raw_expiry[4:6]}-{raw_expiry[6:8]}"
                            else:
                                result["expiry_date"] = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
                            return result
                    else:
                        self.logger.debug(f"Probe Mock HTTP {resp.status}")
            except Exception as e:
                self.logger.debug(f"Probe Mock failed: {e}")
                
        return result

    async def check_duplicate(self, app_key: str) -> bool:
        """
        Check if app_key already exists.
        """
        if not app_key: # Skip for Virtual keys with empty app_key
            return False
            
        for k in self.metadata["keys"]:
            uuid = k["uuid"]
            secure_json = secure_storage.get(f"API_KEY_{uuid}")
            if secure_json:
                try:
                    data = json.loads(secure_json)
                    if data.get("app_key") == app_key:
                        return True
                except:
                    pass
        return False

    def cleanup_duplicates(self) -> int:
        """
        Remove duplicate keys, keeping the most recently created one.
        Returns number of deleted keys.
        """
        seen_app_keys = {} # app_key -> uuid
        duplicates = []
        
        # Sort by creation time (assuming order in list is roughly creation order, or use created_at)
        sorted_keys = sorted(self.metadata["keys"], key=lambda x: x.get("created_at", ""), reverse=True)
        
        keys_to_keep = []
        
        for k in sorted_keys:
            uuid = k["uuid"]
            secure_json = secure_storage.get(f"API_KEY_{uuid}")
            if secure_json:
                try:
                    data = json.loads(secure_json)
                    app_key = data.get("app_key")
                    if app_key in seen_app_keys:
                        duplicates.append(uuid)
                    else:
                        seen_app_keys[app_key] = uuid
                        keys_to_keep.append(k)
                except:
                    keys_to_keep.append(k)
            else:
                keys_to_keep.append(k)

        count = len(duplicates)
        if count > 0:
            for uuid in duplicates:
                self.delete_key(uuid)
            self.logger.info(f"Cleaned up {count} duplicate keys.")
            
        return count

    async def add_key(self, owner: str, key_type: str, account_no: str, app_key: str, secret_key: str, expiry_date: str) -> bool:
        """
        Add a new key.
        """
        # Check duplicate (only for non-virtual)
        if key_type != "VIRTUAL" and await self.check_duplicate(app_key):
            self.logger.warning("Duplicate App Key detected.")
            return False

        if len(self.metadata["keys"]) >= 10:
            self.logger.warning("Max 10 keys allowed.")
            return False

        key_uuid = str(uuid.uuid4())
        
        # For Virtual, generate dummy account number if empty
        if key_type == "VIRTUAL" and not account_no:
            account_no = f"VIRTUAL-{key_uuid[:8]}"
            expiry_date = "9999-12-31" # No expiry for virtual
        
        # Save secure part
        secure_data = json.dumps({"app_key": app_key, "secret_key": secret_key})
        secure_storage.save(f"API_KEY_{key_uuid}", secure_data)

        # Save metadata
        new_key = {
            "uuid": key_uuid,
            "owner": owner,
            "type": key_type, # "MOCK", "REAL", "VIRTUAL"
            "account_no": account_no,
            "expiry_date": expiry_date,
            "created_at": datetime.now().isoformat()
        }
        self.metadata["keys"].append(new_key)
        
        # If first key, make active
        if not self.metadata["active_key_uuid"]:
            self.set_active_key(key_uuid)
        else:
            self._save_metadata()
            
        self.logger.info(f"Key added: {owner} ({key_type})")
        return True

    def delete_key(self, key_uuid: str) -> bool:
        """
        Delete a key.
        """
        # Remove from metadata
        initial_count = len(self.metadata["keys"])
        self.metadata["keys"] = [k for k in self.metadata["keys"] if k["uuid"] != key_uuid]
        
        if len(self.metadata["keys"]) == initial_count:
            self.logger.warning(f"Attempted to delete non-existent key: {key_uuid}")
            return False
        
        # Remove from validation cache
        self._validation_cache.pop(key_uuid, None)
        
        # If active key was deleted, reset active
        if self.metadata["active_key_uuid"] == key_uuid:
            self.metadata["active_key_uuid"] = None
            if self.metadata["keys"]:
                # Set next available as active
                new_active = self.metadata["keys"][0]["uuid"]
                self.set_active_key(new_active)
            else:
                self.logger.info("All keys deleted. No active key.")
        
        self._save_metadata()
        self.logger.info(f"Key deleted: {key_uuid}. Remaining keys: {len(self.metadata['keys'])}")
        return True

    def update_key_owner(self, key_uuid: str, new_owner: str) -> bool:
        """
        Update the owner (alias) of a key.
        """
        target_key = next((k for k in self.metadata["keys"] if k["uuid"] == key_uuid), None)
        if target_key:
            target_key["owner"] = new_owner
            self._save_metadata()
            self.logger.info(f"Key owner updated: {key_uuid} -> {new_owner}")
            return True
        return False

    def set_active_key(self, key_uuid: str):
        """
        Set the currently active key.
        Also updates config MOCK_MODE based on key type.
        """
        target_key = next((k for k in self.metadata["keys"] if k["uuid"] == key_uuid), None)
        if target_key:
            self.metadata["active_key_uuid"] = key_uuid
            self._save_metadata()
            
            # Update Config MOCK_MODE
            # For VIRTUAL, we can treat it as MOCK or keep previous state. 
            # Let's treat VIRTUAL as MOCK for safety (no real trading).
            is_mock = (target_key["type"] in ["MOCK", "VIRTUAL"])
            self._update_config_file(is_mock)
            
            self.logger.info(f"Active key set to: {target_key['owner']} ({target_key['type']})")
            return True
        return False

    def _update_config_file(self, is_mock: bool):
        # Simple yaml update
        settings_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "settings.yaml")
        try:
            lines = []
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            
            new_lines = []
            mock_found = False
            url_found = False
            
            mock_val = "true" if is_mock else "false"
            url_val = "https://mockapi.kiwoom.com" if is_mock else "https://api.kiwoom.com"
            
            for line in lines:
                if line.strip().startswith("MOCK_MODE:"):
                    new_lines.append(f"MOCK_MODE: {mock_val}\n")
                    mock_found = True
                elif line.strip().startswith("KIWOOM_API_URL:"):
                    new_lines.append(f"KIWOOM_API_URL: \"{url_val}\"\n")
                    url_found = True
                else:
                    new_lines.append(line)
            
            if not mock_found:
                new_lines.append(f"MOCK_MODE: {mock_val}\n")
            if not url_found:
                new_lines.append(f"KIWOOM_API_URL: \"{url_val}\"\n")
                
            with open(settings_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
                
        except Exception as e:
            self.logger.error(f"Failed to update config file: {e}")

    def get_keys(self) -> List[Dict]:
        """
        Get list of keys with masked account numbers.
        Masking: Hide first part, show last 4 digits (e.g. ******1234).
        """
        result = []
        for k in self.metadata["keys"]:
            masked_acc = k["account_no"]
            if len(masked_acc) > 4:
                # Mask all except last 4
                masked_acc = "*" * (len(masked_acc) - 4) + masked_acc[-4:]
            
            item = k.copy()
            item["masked_account_no"] = masked_acc
            item["is_active"] = (k["uuid"] == self.metadata["active_key_uuid"])
            item["is_valid"] = self._validation_cache.get(k["uuid"], None) # Add validation status
            result.append(item)
        return result

    def get_active_key(self) -> Optional[Dict]:
        """
        Get the actual AppKey and SecretKey for the active entry.
        Returns dict with app_key, secret_key, type, account_no, etc.
        """
        uuid = self.metadata["active_key_uuid"]
        if not uuid:
            return None
            
        meta = next((k for k in self.metadata["keys"] if k["uuid"] == uuid), None)
        if not meta:
            return None
            
        secure_json = secure_storage.get(f"API_KEY_{uuid}")
        if not secure_json:
            return None
            
        try:
            keys = json.loads(secure_json)
            result = meta.copy()
            result.update(keys)
            return result
        except:
            return None

    def check_expiration(self) -> List[str]:
        """
        Check for keys expiring within 7 days.
        Returns list of warning messages.
        """
        warnings = []
        today = datetime.now()
        for k in self.metadata["keys"]:
            try:
                expiry = datetime.strptime(k["expiry_date"], "%Y-%m-%d")
                days_left = (expiry - today).days
                if 0 <= days_left <= 7:
                    warnings.append(f"[{k['owner']}] Key expires in {days_left} days ({k['expiry_date']})")
                elif days_left < 0:
                    warnings.append(f"[{k['owner']}] Key EXPIRED on {k['expiry_date']}")
            except:
                pass
        return warnings

    def get_expiry_alert_days(self) -> int:
        return self.metadata.get("expiry_alert_days", 7)

    def set_expiry_alert_days(self, days: int):
        self.metadata["expiry_alert_days"] = days
        self._save_metadata()

    def is_auto_login_enabled(self) -> bool:
        return self.metadata.get("auto_login_enabled", False)

    def set_auto_login_enabled(self, enabled: bool):
        self.metadata["auto_login_enabled"] = enabled
        self._save_metadata()

    async def verify_key_by_uuid(self, uuid: str) -> bool:
        """
        Verify a specific key by UUID.
        Updates expiry_date if verification is successful.
        """
        meta = next((k for k in self.metadata["keys"] if k["uuid"] == uuid), None)
        if not meta:
            self._validation_cache[uuid] = False
            return False
            
        secure_json = secure_storage.get(f"API_KEY_{uuid}")
        if not secure_json:
            self._validation_cache[uuid] = False
            return False
            
        try:
            keys = json.loads(secure_json)
            app_key = keys["app_key"]
            secret_key = keys["secret_key"]
            
            # Skip probe for VIRTUAL keys
            if meta.get("type") == "VIRTUAL":
                self._validation_cache[uuid] = True
                return True
            
            # Use probe_key_info to get details including expiry
            info = await self.probe_key_info(app_key, secret_key)
            
            if info["valid"]:
                self.logger.info(f"Probe successful for {uuid}. Expiry: {info['expiry_date']}")
                # Update metadata if changed
                changed = False
                if info["expiry_date"] and meta["expiry_date"] != info["expiry_date"]:
                    self.logger.info(f"Updating expiry for {uuid}: {meta['expiry_date']} -> {info['expiry_date']}")
                    meta["expiry_date"] = info["expiry_date"]
                    changed = True
                else:
                    self.logger.info(f"Expiry unchanged for {uuid}: {meta['expiry_date']}")
                
                # Also update type if for some reason it mismatch (though unlikely if probed correctly)
                if info["type"] and meta["type"] != info["type"]:
                    meta["type"] = info["type"]
                    changed = True
                    
                if changed:
                    self._save_metadata()
                
                self._validation_cache[uuid] = True
                return True
            
            self._validation_cache[uuid] = False
            return False
        except:
            self._validation_cache[uuid] = False
            return False

    def check_active_key_expiration(self) -> Optional[str]:
        """
        Check expiration for the ACTIVE key only.
        Returns warning message if expiring within configured days or expired, else None.
        """
        uuid = self.metadata["active_key_uuid"]
        if not uuid:
            return None
            
        k = next((k for k in self.metadata["keys"] if k["uuid"] == uuid), None)
        if not k:
            return None
            
        try:
            expiry = datetime.strptime(k["expiry_date"], "%Y-%m-%d")
            today = datetime.now()
            days_left = (expiry - today).days
            
            alert_days = self.get_expiry_alert_days()
            
            if 0 <= days_left <= alert_days:
                return f"활성 키 [{k['owner']}] 만료 {days_left}일 전입니다 ({k['expiry_date']})"
            elif days_left < 0:
                return f"활성 키 [{k['owner']}]가 만료되었습니다 ({k['expiry_date']})"
        except:
            pass
        return None

key_manager = KeyManager()
