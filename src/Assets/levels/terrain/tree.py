from direct.showbase.ShowBase import ShowBase

def get_all_nodepaths(root_np):
    """
    Retourne une liste de tous les NodePath
    à partir de root_np (ex: render), enfants inclus.
    """
    nodes = []

    def traverse(np):
        nodes.append(np)
        for child in np.getChildren():
            traverse(child)

    traverse(root_np)
    return nodes

app = ShowBase()
model = loader.loadModel("models/levelfun.bam")
model.reparentTo(render)

all_nodes = get_all_nodepaths(render)

print(f"{len(all_nodes)} NodePath trouvés")

for np in all_nodes:
    print(np, np.getName(), np.node().__class__.__name__)

app.run()