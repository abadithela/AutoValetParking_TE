from components.boxcomponent import BoxComponent
import trio
from variables.global_vars import *
from prepare.communication import *
import motiontracking.mpc_tracking as tracking
import math
from components.game import Game
import random
sys.path.append('/anaconda3/lib/python3.7/site-packages')
from shapely.geometry import Polygon
from shapely import affinity
from ipdb import set_trace as st

class State:
    """
    vehicle state class
    """

    def __init__(self, x=0.0, y=0.0, yaw=0.0, v=0.0):
        self.x = x
        self.y = y
        self.yaw = yaw
        self.v = v

class Car(BoxComponent):
    def __init__(self, arrive_time, depart_time):
        super().__init__()
        self.name = 'Car {}'.format(id(self))
        self.arrive_time = arrive_time
        self.depart_time = depart_time
        self.ref = None
        self.x = START_X
        self.y = START_Y
        self.yaw = START_YAW
        self.v = 0.0
        self.state = State(x=self.x, y=self.y, yaw=self.yaw, v=self.v)
        self.status = 'Idle'
        self.last_segment = False
        self.direction = 1
        self.delay = 0
        self.unparking = False
        self.waiting = False
        self.replan = False
        self.close = False
        self.parking = True
        self.retrieving = False
        self.is_at_pickup = False
        self.parked = False
        self.cancel = False

    async def update_planner_command(self,send_response_channel,Game):
        async with self.in_channels['Planner']:
            async for directive in self.in_channels['Planner']:
                if directive == 'Wait':
                    print('{0} - Receiving Directive from Planner to wait'.format(self.name))
                    self.status = 'Waiting'
                elif directive == 'Back2spot':
                    print('{0} - Receiving Directive from Planner to drive back into the spot'.format(self.name))
                    directive = self.ref[:][0]
                    directive = [np.flip(directive, 0)]
                    # self.ref = directive
                    #print(directive[-1])
                    direc = [[self.x/SCALE_FACTOR_PLAN, self.y/SCALE_FACTOR_PLAN, -1*np.rad2deg(self.yaw)]]
                    direc.append([directive[-1][-1][0], directive[-1][-1][1], directive[-1][-1][2]] )
                    directive = [np.array(direc)]
                    self.ref = directive
                    print('Tracking this path:')
                    print(self.ref)
                    # st()
                    self.replan = True
                    self.last_segment = True
                    self.direction = 1
                    await self.track_reference(Game,send_response_channel)
                    await trio.sleep(0)
                else:
                    print('{0} - Receiving Directive from Planner'.format(self.name))
                    #self.status = 'Replan'
                    self.ref = np.array(directive)
                    #if self.replan:
                    #print('Tracking this path:')
                    #print(directive)
                    #if directive=='Unpark':
                    #self.unparking = True
                    await self.track_reference(Game,send_response_channel)
                    await trio.sleep(0)
                    #await self.send_response(send_response_channel)

    async def iterative_linear_mpc_control(self, xref, x0, dref, oa, od):
        if oa is None or od is None:
            oa = [0.0] * tracking.T
            od = [0.0] * tracking.T
        for i in range(tracking.MAX_ITER):
            xbar = tracking.predict_motion(x0, oa, od, xref)
            poa, pod = oa[:], od[:]
            oa, od, _, _, _, _ = tracking.linear_mpc_control(xref, xbar, x0, dref)
            du = sum(abs(oa - poa)) + sum(abs(od - pod))  # calc u change value
            if du <= tracking.DU_TH:
                break
        return oa, od

    async def track_async(self, cx, cy, cyaw, ck, sp, dl, initial_state,goalspeed,Game,send_response_channel): # modified from MPC
        goal = [cx[-1], cy[-1]]
        self.state = initial_state
        # initial yaw compensation
        if self.state.yaw - cyaw[0] >= math.pi:
            self.state.yaw -= math.pi * 2.0
        elif self.state.yaw - cyaw[0] <= -math.pi:
            self.state.yaw += math.pi * 2.0
        time = 0.0
        target_ind, _ = tracking.calc_nearest_index(self.state, cx, cy, cyaw, 0)
        odelta, oa = None, None
        cyaw = tracking.smooth_yaw(cyaw)
        self.waiting = False
        blocked = False
        while tracking.MAX_TIME >= time:
            while not self.path_clear(Game) or blocked:
                #self.status = 'Stop'
                print('{0} stops because path is blocked'.format(self.name))
                _, conflict_cars, failed, conflict, blocked = self.check_path(Game)
                #print(conflict_cars)
                #print(failed)
                #print(self.waiting)
                #if not self.status == 'Waiting':
                if conflict and not self.waiting:
                    self.status = 'Conflict'
                    #send response to sup
                    print('We have a conflict')
                    await self.send_conflict(conflict_cars, send_response_channel)
                    self.waiting = True
                        # return
                if failed or blocked and not self.waiting and not self.replan:
                    #send response to sup
                    self.status = 'Blocked'
                    print('Blocked by a failure')
                    await self.send_response(send_response_channel)
                    self.waiting = True
                    # return
                if self.status == 'Replan':
                    print('{0} Stopping the Tracking'.format(self.name))
                    self.v = 0
                    return
                await trio.sleep(3)
            self.status = 'Driving'
            self.waiting = False
            xref, target_ind, dref = tracking.calc_ref_trajectory(self.state, cx, cy, cyaw, ck, sp, dl, target_ind)
            x0 = [self.state.x, self.state.y, self.state.v, self.state.yaw]  # current state
            oa, odelta = await self.iterative_linear_mpc_control(xref, x0, dref, oa, odelta)
            if odelta is not None:
                di, ai = odelta[0], oa[0]
            self.state = tracking.update_state(self.state, ai, di)
            time = time + tracking.DT
            self.x = self.state.x
            self.y = self.state.y
            self.yaw = self.state.yaw
            self.v = self.state.v
            await trio.sleep(0)
            if tracking.check_goal(self.state, goal, target_ind, len(cx),goalspeed,self.last_segment): # modified goal speed
                break
 
    async def track_reference(self,Game,send_response_channel):
        now = trio.current_time()
        if self.depart_time <= now:
            self.delay = self.depart_time-now
        print('{0} - Tracking reference...'.format(self.name))
        self.close = False
        ck = 0 
        dl = 1.0  # course tick
        if not self.status == 'Replan':
            try:
                self.check_if_car_is_in_spot(Game)
            except: 
                st()
            if self.check_if_car_is_in_spot(Game):
                print('Car is in a parking spot')
                self.parked = True
                while not self.check_clear_before_unparking(Game):
                    await trio.sleep(0.1)
        self.status = 'Driving'
        self.parked = False
        # including a failure in 20% of cars
        failidx = len(self.ref)
        chance = random.randint(1,100) # changed to 0!!!
        if not self.replan:
            if len(self.ref)-1>4 and chance <=0:
                failidx = np.random.randint(low=4, high=6, size=1)
                if self.parking:
                    print('{0} will fail at acceptable spot: {1}'.format(self.name,failidx))
                else:
                    print('{0} will fail in narrow path: {1}'.format(self.name,failidx))
            elif len(self.ref)-1>10 and chance <=0:
                failidx = np.random.randint(low=len(self.ref)-5, high=len(self.ref)-1, size=1)
                if self.parking:
                    print('{0} will fail in narrow path: {1}'.format(self.name,failidx))
                else:
                    print('{0} will fail at acceptable spot: {1}'.format(self.name,failidx))
        # start tracking segments
        for i in range(0,len(self.ref)-1):
            #print('{0} self.unparking'.format(self.name))
            #print(self.unparking)
            if (i==failidx):
                print('{0} Failing'.format(self.name))
                await self.failure(send_response_channel)
                return  
            if i >= 1:
                self.unparking = False
            self.close = False
            if self.check_car_close_2_spot(Game):
                self.close = True
            self.status = 'Driving'
            path = self.ref[:][i]
            cx = path[:,0]*SCALE_FACTOR_PLAN
            cy = path[:,1]*SCALE_FACTOR_PLAN
            cyaw = np.deg2rad(path[:,2])*-1
            state = np.array([self.x, self.y,self.yaw])
            #  check  direction of the segment
            self.direction = tracking.check_direction(path) 
            sp = tracking.calc_speed_profile(cx, cy, cyaw, TARGET_SPEED,TARGET_SPEED,self.direction)
            initial_state = State(x=state[0], y=state[1], yaw=state[2], v=self.v)
            await self.track_async(cx, cy, cyaw, ck, sp, dl, initial_state,TARGET_SPEED,Game,send_response_channel)
            await trio.sleep(0)
            if self.status == 'Replan':
                return
        if not self.status == 'Failure':
            self.last_segment = True
            state = np.array([self.x, self.y,self.yaw])
            path = self.ref[:][-1]
            cx = path[:,0]*SCALE_FACTOR_PLAN
            cy = path[:,1]*SCALE_FACTOR_PLAN
            cyaw = np.deg2rad(path[:,2])*-1
            self.direction = tracking.check_direction(path)
            initial_state = State(x=state[0], y=state[1], yaw=state[2], v=self.v)
            sp = tracking.calc_speed_profile(cx, cy, cyaw, TARGET_SPEED/2,0.0,self.direction)
            await self.track_async(cx, cy, cyaw, ck, sp, dl, initial_state,0.0,Game,send_response_channel)
            if self.status == 'Replan':
                return
            self.status = 'Completed'
            self.is_at_pickup = self.check_at_pickup(Game)
            if self.is_at_pickup:
                self.retrieving = False
            self.last_segment = False
            if self.check_if_car_is_in_spot(Game):
                self.parked = True
            self.parking = False
            await self.send_response(send_response_channel)

    async def send_response(self,send_response_channel):
        await trio.sleep(1)
        response = self.status
        print('{0} - sending {1} response to Planner'.format(self.name,response))
        await send_response_channel.send((self,response))
        await trio.sleep(1)

    async def send_conflict(self,cars,send_response_channel):
        response = (self.status,cars)
        print('{0} - sending {1} response to Planner'.format(self.name,response))
        await send_response_channel.send((self,response))
        await trio.sleep(1)

    def path_clear(self, gme):
        clear, _, _ ,_,_= self.check_path(gme)
        return clear
    
    def check_clear_before_unparking(self,gme):
        self.unparking = True
        clear = gme.clear_before_unparking(self)
        return clear

    def check_car_close_2_spot(self,gme):
        close = gme.is_car_close_2_spot(self)
        return close

    def check_at_pickup(self,gme):
        at_pickup = gme.is_car_at_pickup(self)
        return at_pickup

    def check_path(self, gme):
        #print('Checking the path')
        clear, conflict_cars, failed, conflict, blocked = gme.check_car_path(self)
        return clear, conflict_cars, failed, conflict, blocked

    def check_if_car_is_in_spot(self,gme):
        in_spot = gme.is_car_in_spot(self)
        return in_spot

    async def stop(self,send_response_channel):
        self.status = 'Stop'
        await self.send_response(send_response_channel)

    async def failure(self,send_response_channel):
        self.status = 'Failure'
        await self.send_response(send_response_channel)
        await trio.sleep(1000) # freeze car

    async def run(self,send_response_channel,Game):
        async with trio.open_nursery() as nursery:
            nursery.start_soon(self.update_planner_command,send_response_channel,Game)
            if self.cancel:
                print('Cancelling {0}'.format(self.name))
                nursery.cancel_scope.cancel()
            await trio.sleep(0)