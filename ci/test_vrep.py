import pypot
from poppy.creatures import PoppyHumanoid

poppy = 0
i = 0
while poppy == 0 and i < 4:
    i += 1
    try:
        poppy = PoppyHumanoid(simulator='vrep', host='localhost')
        print('Test connection ', i)
        break
    except:
        print('close_all_connections')
        pypot.vrep.close_all_connections()
        pass
print poppy.get_object_position('pelvis_visual')
