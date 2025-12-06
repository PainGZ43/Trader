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

def generate_detailed_simplified_diagram():
    set_korean_font()
    
    G = nx.DiGraph()

    # Define nodes with more detail but grouped
    nodes = {
        # External
        "Kiwoom": "키움증권 API\n(External)",
        
        # Data Layer
        "WSClient": "WebSocket Client\n(실시간 수신)",
        "DataCol": "Data Collector\n(데이터 가공/분봉)",
        
        # Strategy Layer
        "StratEng": "Strategy Engine\n(전략 실행)",
        "AI": "AI / Indicators\n(분석/예측)",
        
        # Execution Layer
        "RiskMgr": "Risk Manager\n(리스크 검증)",
        "OrderMgr": "Order Manager\n(주문 생성/관리)",
        
        # UI/User
        "User": "사용자\n(User)",
        "UI": "UI / Dashboard\n(모니터링)"
    }

    G.add_nodes_from(nodes.keys())

    # Define linear flow edges
    edges = [
        # Data Flow
        ("Kiwoom", "WSClient"),
        ("WSClient", "DataCol"),
        
        # Strategy Flow
        ("DataCol", "StratEng"),
        ("StratEng", "AI"),
        ("AI", "StratEng"), # Return prediction
        
        # Execution Flow
        ("StratEng", "RiskMgr"), # Signal
        ("RiskMgr", "OrderMgr"), # Validated Signal
        ("OrderMgr", "Kiwoom"),  # Order
        
        # Feedback/UI
        ("Kiwoom", "OrderMgr"), # Execution Confirm (simplified return path)
        ("DataCol", "UI"),
        ("OrderMgr", "UI"),
        ("User", "UI")
    ]
    
    G.add_edges_from(edges)

    # Custom layout for "swimlane" style linear flow
    # x=Layer, y=Vertical position
    pos = {
        "Kiwoom": (0, 1),
        
        "WSClient": (1, 1.5),
        "DataCol": (1.5, 1.5),
        
        "StratEng": (2.5, 1.5),
        "AI": (2.5, 0.5),
        
        "RiskMgr": (3.5, 1.5),
        "OrderMgr": (4, 1.5),
        
        "UI": (2.5, 2.5),
        "User": (2.5, 3.2)
    }
    
    plt.figure(figsize=(16, 9))
    
    # Draw nodes
    # Color coding by layer
    colors = []
    for n in G.nodes():
        if n in ["Kiwoom", "User"]: colors.append('lightgray')
        elif n in ["WSClient", "DataCol"]: colors.append('lightblue') # Data
        elif n in ["StratEng", "AI"]: colors.append('lightgreen') # Strategy
        elif n in ["RiskMgr", "OrderMgr"]: colors.append('lightcoral') # Execution
        else: colors.append('wheat') # UI

    nx.draw_networkx_nodes(G, pos, node_size=3500, node_color=colors, edgecolors='black', linewidths=1)
    
    # Draw edges
    nx.draw_networkx_edges(G, pos, width=1.5, arrowsize=20, arrowstyle='->', connectionstyle="arc3,rad=0.1")
    
    # Draw labels
    labels = {k: v for k, v in nodes.items() if k in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels, font_size=9, font_family="Malgun Gothic", font_weight="bold")

    # Add edge labels
    edge_labels = {
        ("Kiwoom", "WSClient"): "Tick",
        ("WSClient", "DataCol"): "Raw",
        ("DataCol", "StratEng"): "Candle",
        ("StratEng", "RiskMgr"): "Signal",
        ("RiskMgr", "OrderMgr"): "Valid",
        ("OrderMgr", "Kiwoom"): "Order"
    }
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_family="Malgun Gothic", font_size=8)

    # Add layer annotations
    plt.text(1.25, 0, "Data Layer", fontsize=12, ha='center', fontweight='bold', color='blue')
    plt.text(2.5, 0, "Strategy Layer", fontsize=12, ha='center', fontweight='bold', color='green')
    plt.text(3.75, 0, "Execution Layer", fontsize=12, ha='center', fontweight='bold', color='red')

    plt.title("상세 시스템 구조도 (Detailed Architecture Flow)", fontsize=15)
    plt.axis('off')
    plt.margins(0.1)
    
    # Ensure output directory exists
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "images")
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, "detailed_simplified_flow.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Detailed diagram saved to {output_path}")

if __name__ == "__main__":
    generate_detailed_simplified_diagram()
