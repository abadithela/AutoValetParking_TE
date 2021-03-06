import trio
import numpy as np

def get_current_time(start_time):
    return trio.current_time() - start_time

def create_unidirectional_channel(sender, receiver, max_buffer_size, name = False):
    out_channel, in_channel = trio.open_memory_channel(max_buffer_size)
    if name:
        sender.out_channels[name] = out_channel
        receiver.in_channels[name] = in_channel
    else:
        sender.out_channels[receiver.name] = out_channel
        receiver.in_channels[sender.name] = in_channel

def create_bidirectional_channel(compA, compB, max_buffer_size):
    create_unidirectional_channel(sender=compA, receiver=compB, max_buffer_size=max_buffer_size)
    create_unidirectional_channel(sender=compB, receiver=compA, max_buffer_size=max_buffer_size)

def set_up_channels(supervisor,planner, game, map_sys, customer, simulation):
        create_bidirectional_channel(supervisor,planner,max_buffer_size=np.inf)
        create_bidirectional_channel(customer, supervisor, max_buffer_size=np.inf)
        create_unidirectional_channel(sender=customer, receiver=supervisor, max_buffer_size=np.inf, name='Request')
        create_unidirectional_channel(sender=game, receiver=map_sys, max_buffer_size=np.inf, name='Enter')
        create_unidirectional_channel(sender=game, receiver=map_sys, max_buffer_size=np.inf, name='Exit')
        #create_unidirectional_channel(sender=game, receiver=map_sys, max_buffer_size=np.inf, name='PedEnter')
        create_bidirectional_channel(map_sys, planner, max_buffer_size=np.inf)
        create_unidirectional_channel(sender=supervisor, receiver=game, max_buffer_size=np.inf, name='GameEnter')
        create_unidirectional_channel(sender=supervisor, receiver=game, max_buffer_size=np.inf, name='GameExit')
        create_unidirectional_channel(sender=supervisor, receiver=game, max_buffer_size=np.inf, name='GameEnterPeds')
        create_unidirectional_channel(sender=game, receiver=simulation, max_buffer_size=np.inf)
        create_unidirectional_channel(sender=game, receiver=simulation, max_buffer_size=np.inf, name='PedSimulation')
        create_unidirectional_channel(sender=game, receiver=simulation, max_buffer_size=np.inf, name='ExitSim')
        create_unidirectional_channel(sender=supervisor, receiver= game, max_buffer_size=np.inf,name='Failure')
