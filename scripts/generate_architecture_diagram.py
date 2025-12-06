import matplotlib.pyplot as plt
import networkx as nx
import os
from matplotlib import font_manager, rc

def set_korean_font():
    """Sets a Korean-compatible font for matplotlib."""
    font_name = "Malgun Gothic" # Standard Korean font on Windows
    try:
        rc('font', family=font_name)
        plt.rcParams['axes.unicode_minus'] = False
    except Exception as e:
        print(f"Warning: Could not set font {font_name}. Labels may not render correctly. Error: {e}")

def generate_diagram():
    set_korean_font()
    
    G = nx.DiGraph()

    # Define nodes with Korean labels
    nodes = {
        "User": "사용자 (User)",
        "KiwoomAPI": "키움증권 Open API",
        "KakaoAPI": "카카오톡 API",
        "WSClient": "WebSocket Client\n(실시간 시세)",
        "RESTClient": "Kiwoom REST Client\n(계좌/주문/과거데이터)",
        "DataCol": "DataCollector\n(캔들 생성/버퍼링)",
        "MacroCol": "MacroCollector\n(환율/지수)",
        "EventBus": "EventBus\n(Pub/Sub)",
        "StratEng": "Strategy Engine",
        "AI": "AI Engine\n(예측/분석)",
        "ExecEng": "Execution Engine",
        "RiskMgr": "Risk Manager\n(리스크 관리)",
        "OrderMgr": "Order Manager\n(주문 처리)",
        "AcctMgr": "Account Manager\n(잔고 동기화)",
        "Noti": "Notification Manager",
        "Dashboard": "Real-time Dashboard",
        "LogView": "Log Viewer",
        "DB": "Database (SQLite)"
    }

    G.add_nodes_from(nodes.keys())

    # Define edges
    edges = [
        ("User", "Dashboard"),
        ("KiwoomAPI", "WSClient"),
        ("KiwoomAPI", "RESTClient"),
        ("WSClient", "DataCol"),
        ("RESTClient", "DataCol"),
        ("DataCol", "EventBus"),
        ("MacroCol", "EventBus"),
        ("EventBus", "StratEng"),
        ("StratEng", "AI"),
        ("StratEng", "ExecEng"),
        ("ExecEng", "RiskMgr"),
        ("RiskMgr", "OrderMgr"),
        ("OrderMgr", "RESTClient"),
        ("RESTClient", "AcctMgr"),
        ("AcctMgr", "EventBus"),
        ("EventBus", "Noti"),
        ("Noti", "KakaoAPI"),
        ("EventBus", "Dashboard"),
        ("EventBus", "LogView"),
        ("EventBus", "DB")
    ]
    
    G.add_edges_from(edges)

    # Position nodes (using a layout or manual positions for better structure)
    # Using a shell layout for layers or spring layout
    pos = nx.spring_layout(G, seed=42, k=2) 
    
    plt.figure(figsize=(14, 10))
    
    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_size=3000, node_color='lightblue', alpha=0.9)
    
    # Draw edges
    nx.draw_networkx_edges(G, pos, width=1.5, alpha=0.6, arrowsize=20)
    
    # Draw labels
    labels = {k: v for k, v in nodes.items() if k in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels, font_size=9, font_family="Malgun Gothic")

    plt.title("PainTrader 시스템 아키텍처", fontsize=15)
    plt.axis('off')
    
    # Ensure output directory exists
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "images")
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, "architecture_diagram.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Diagram saved to {output_path}")

if __name__ == "__main__":
    generate_diagram()
