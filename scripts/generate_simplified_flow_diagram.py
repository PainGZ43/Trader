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

def generate_simplified_diagram():
    set_korean_font()
    
    G = nx.DiGraph()

    # Define nodes for the simplified flow
    nodes = {
        "Kiwoom": "키움증권 API\n(Broker)",
        "Data": "데이터 계층\n(Data Layer)\n수집/가공",
        "Strategy": "전략 계층\n(Strategy Layer)\n판단/신호",
        "Execution": "실행 계층\n(Execution Layer)\n주문/관리",
        "User": "사용자\n(User)"
    }

    G.add_nodes_from(nodes.keys())

    # Define edges for the linear flow
    edges = [
        ("Kiwoom", "Data"),       # Raw Data
        ("Data", "Strategy"),     # Market Events
        ("Strategy", "Execution"),# Trade Signals
        ("Execution", "Kiwoom"),  # Orders
        ("User", "Execution"),    # Manual Control
        ("Execution", "User")     # Notifications/Status
    ]
    
    G.add_edges_from(edges)

    # Custom layout for a linear left-to-right flow
    pos = {
        "Kiwoom": (0, 1),
        "Data": (1, 1),
        "Strategy": (2, 1),
        "Execution": (3, 1),
        "User": (3, 0)
    }
    
    plt.figure(figsize=(12, 6))
    
    # Draw nodes
    # Color coding: External=Gray, Core=Blue
    node_colors = ['lightgray' if n in ["Kiwoom", "User"] else 'lightblue' for n in G.nodes()]
    
    nx.draw_networkx_nodes(G, pos, node_size=4000, node_color=node_colors, edgecolors='black', linewidths=1)
    
    # Draw edges
    nx.draw_networkx_edges(G, pos, width=2, arrowsize=25, arrowstyle='->', connectionstyle="arc3,rad=0.1")
    
    # Draw labels
    labels = {k: v for k, v in nodes.items() if k in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels, font_size=10, font_family="Malgun Gothic", font_weight="bold")

    # Add edge labels to explain the flow
    edge_labels = {
        ("Kiwoom", "Data"): "실시간 시세",
        ("Data", "Strategy"): "Market Event\n(틱/캔들)",
        ("Strategy", "Execution"): "Trade Signal\n(매수/매도)",
        ("Execution", "Kiwoom"): "주문 전송",
        ("User", "Execution"): "제어/감시"
    }
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_family="Malgun Gothic", font_size=8)

    plt.title("개선된 시스템 플로우 (Simplified Architecture)", fontsize=15)
    plt.axis('off')
    plt.margins(0.2)
    
    # Ensure output directory exists
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "images")
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, "simplified_flow_diagram.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Simplified diagram saved to {output_path}")

if __name__ == "__main__":
    generate_simplified_diagram()
