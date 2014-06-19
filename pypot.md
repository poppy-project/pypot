# Pypot todo list

## Documentation
- [ ] Déplacer la doc. de construction d'un ergo-robot à un endroit accessible + post de blog
- [ ] Post sur le forum pour expliquer comment Pypot pourrait être adapté à d'autres types de moteur

## Trajectory
- [ ] class trajectoire plus compacte et avec timestamp
- [ ] +/- compatible avec les trajectoires ROS de Baxter?

## GUI
- [ ] User interfaces are implemented in HTML and Javascript, utilizing the ROS-Bridge web interface ???
- [ ] HOP pour robot à cable (parler à Ludo)

## Most likely raised during interpreter shutdown
- [ ] http://bugs.python.org/issue14623
- [ ] en python 3 ça doit marcher !
- [ ] technique serial (pas bien propre mais efficace):
    ```python
def __del__(self):
    """Destructor.  Calls close()."""
    # The try/except block is in case this is called at program
    # exit time, when it's possible that globals have already been
    # deleted, and then the close() call might fail.  Since
    # there's nothing we can do about such failures and they annoy
    # the end users, we suppress the traceback.
    try:
        self.close()
    except:
        pass
    ```
