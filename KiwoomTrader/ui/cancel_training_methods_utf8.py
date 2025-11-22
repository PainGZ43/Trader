
    def cancel_training(self):
        """Cancel AI training"""
        self.training_cancel_flag = True
        self.train_stop_btn.setEnabled(False)
        self.train_result_text.append("\n Stop training...\n")
        self.log("AI Training cancel requested")
    
    def _finish_training(self, success):
        """Restore UI after training completion"""
        self.train_start_btn.setEnabled(True)
        self.train_stop_btn.setEnabled(False)
        if not success:
            self.train_progress.setVisible(False)
