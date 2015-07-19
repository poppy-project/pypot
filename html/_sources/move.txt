.. _move:

Move recording and playing
==========================

The :mod:`~pypot.primitive.move` module contains utility classes to help you record and play moves. Those :class:`~pypot.primitive.move.Move` is simply defined as a sequence of positions.

.. note:: To keep the :mod:`~pypot.primitive.move` module as simple as possible, you can only define :class:`~pypot.primitive.move.Move` as a predefined frequency and you can not define keyframes whenever you want. This could be added if it seems like it would be useful.

You can use the :mod:`~pypot.primitive.move` module to:

* record moves,
* play moves,
* save/load them on the disk.

The :class:`~pypot.primitive.move.MoveRecorder` and :class:`~pypot.primitive.move.MovePlayer` are defined as subclass of :class:`~pypot.primitive.primitive.LoopPrimitive` and can thus be used as such. For instance, if you want to record a 50Hz move on all the motor of an ergo-robot you can simply use the following code::

    import time
    import pypot.robot

    from pypot.primitive.move import MoveRecorder, Move, MovePlayer

    ergo = pypot.robot.from_config(...)

    move_recorder = MoveRecorder(ergo, 50, ergo.motors)

    ergo.compliant = True

    move_recorder.start()
    time.sleep(5)
    move_recorder.stop()

This move can then be saved on disk::

    with open('my_nice_move.move', 'w') as f:
        move_recorder.move.save(f)

And loaded and replayed::

    with open('my_nice_move.move') as f:
        m = Move.load(f)

    ergo.compliant = False

    move_player = MovePlayer(ergo, m)
    move_player.start()

.. warning:: It is important to note that you should be sure that you primitive actually runs at the same speed that the move has been recorded. If the player can not run as fast as the framerate of the recorded :class:`~pypot.primitive.move.Move`, it will be played slowly resulting in a slower version of your move.
