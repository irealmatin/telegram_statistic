import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Union

import demoji
from loguru import logger
from pyvis.network import Network


class ChatGraph:
    """Generates Graph from a telegram chat json file
    """
    def __init__(self, chat_json: Union[str, Path]):
        """
        :param chat_json: path to telegram export json file
        """
        # load chat data
        logger.info(f"Loading chat data from {chat_json}...")
        with open(chat_json) as f:
            self.chat_data = json.load(f)

    def red2blue(self, n: int):
        """
        This method generates n colors from the red to blue
        spectrum and returns them as a list of hex-colors.
        """
        colors = []
        d = 256 / n
        for i in range(n):
            rgb = (int(256 - (d * i)), 0, int(d * i))
            colors.append('#%02x%02x%02x' % rgb)
        return colors

    def generate_graph(self, output_graph_path: Union[str, Path], top_n: int = None):
        """Generates a Graph from the chat data

        :param output_graph_path: path to output directory for graph image
        :param top_n: number of top users to include in graph
        """
        logger.info("Loading reply messages...")
        messages = iter(self.chat_data['messages'])
        users = {}
        message_writer = {}
        conections = defaultdict(int)
        interactions = defaultdict(int)

        for message in messages:
            # Exclude non-message contents from the scope of our analysis.
            if message['type'] == 'message':
                # Store the ID and name of each user in users dictionary.
                if (
                    message["from_id"] not in users and
                    message["from"] is not None
                ):
                    users[message["from_id"]] = demoji.replace(message["from"], "")
                # Define who wrote each message in
                # this part and keep his/her ID.
                message_writer[message["id"]] = message["from_id"]
            if "reply_to_message_id" in message:
                # Figure out who the responder was.
                reply_from = message["from_id"]
                # Figure out who this replay was targeted for.
                reply_to_id = message["reply_to_message_id"]
                if reply_to_id in message_writer:
                    reply_to = message_writer[reply_to_id]
                # In conections dictionary, we keep track the amount of
                # interactions that exist between two persons.
                # It should be noted that (userA, userB)
                # differs from (userB, userA).
                conections[(reply_from, reply_to)] += 1
                # Increase the interaction  of anyone
                # who has replayed a message or  received a reply
                interactions[reply_from] += 1
                interactions[reply_to] += 1

        logger.info("Generating graph...")
        # Set a value for our nodes.
        # Here we consider the interaction of each
        # person as the value of that node.
        node_value = []
        for user in users.keys():
            # Consider the value 1 for Nodes that
            # have not interacted with others.
            if user not in interactions:
                node_value.append(1)
            # Consider the value of interaction + 1 for other nodes.
            else:
                node_value.append(interactions[user] + 1)
        sorted_node_value = sorted(node_value, reverse=True)

        # Create color based on the amount of nodes.
        colors = self.red2blue(len(users))
        # Match the colors to the values of each node in this section.
        value_color_dict = {}
        for i in range(len(colors)):
            value_color_dict[sorted_node_value[i]] = colors[i]
        users_color = list(map(lambda x: value_color_dict[x], node_value))

        # Generate graph
        G = Network(height='100%', width='100%')
        # Add all nodes to the graph.
        G.add_nodes(
            list(users.keys()),
            title=list(users.values()),
            value=node_value,
            label=list(users.values()),
            color=users_color
        )

        # only show most active users and their connections in the graph
        if top_n is not None:
            logger.info(f"Filtering by top {top_n} users...")
            interaction_count = defaultdict(int)
            for (node_a, node_b), weight in conections.items():
                interaction_count[node_a] += weight
                interaction_count[node_b] += weight

            active_users = Counter(interaction_count).most_common(top_n)
            active_users = [x[0] for x in active_users]

        # Add all edges to the graph.
        for node_a, node_b in conections:
            if (top_n is None) or not any([node_a in active_users, node_b in active_users]):
                continue

            nodes = G.get_nodes()
            if node_a not in nodes or node_b not in nodes:
                continue
            G.add_edge(node_a, node_b)

        # Generate the graph with the necessary options.
        options = json.load(open("src/graph_options.json"))
        G.set_options(f'var options = {json.dumps(options)}')
        G.show(str(Path(output_graph_path)))
        logger.info(f"Saved graph to {output_graph_path}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--chat_json", help="Path to telegram export json file")
    parser.add_argument("--output_graph_path", help="Path to output directory for graph image")
    parser.add_argument("--top_n", help="Number of top users to show in the graph", type=int)
    args = parser.parse_args()

    chat_graph = ChatGraph(chat_json=args.chat_json)
    chat_graph.generate_graph(output_graph_path=args.output_graph_path, top_n=args.top_n)
    
