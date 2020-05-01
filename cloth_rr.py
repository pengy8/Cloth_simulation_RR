#Simple example Robot Raconteur webcam service

#Note: This example is intended to demonstrate Robot Raconteur
#and is designed to be simple rather than optimal.

import time
import RobotRaconteur as RR
#Convenience shorthand to the default node.
#RRN is equivalent to RR.RobotRaconteurNode.s
RRN=RR.RobotRaconteurNode.s
import _thread
import threading
import numpy
import traceback
import cv2
import platform
import sys
import argparse


from cloth_rr_lib import *

#Class that implements a single webcam
class Cloth_impl(object):
    #Init the camera being passed the camera number and the camera name

    
    def __init__(self):
        
        self._lock=threading.RLock()
        
        self.pose = None
        
        try:
            t1 = threading.Thread(target=self.read_loop(), args=())
            t1.start()
            #_thread.start_new_thread(self.read_loop(),())
        except:
           print ("Error: unable to start thread")        



    def read_loop(self):
        #with self._lock:
        
            clock = pygame.time.Clock()
            
            while True:
            #for i in range(1000):
                tic = timeit.default_timer()
                if not get_input(): break
        
                pos = []
                for x in range(point_n):
                    for y in range(point_n):
                            pos.append(np.array(cloth.particles[x][y].pos))     
                            
                self.pose = np.array(pos)          
                #print self.pose.flatten('C')   
        #        return list(pos.flatten('C'))
                
                draw()
                clock.tick(target_fps)
                
            #print (np.mean(t_all),np.std(t_all))    
            pygame.quit()
        
    def getpose(self):
        #self.pose = self.k4a.get_pose()
        with self._lock:
            return list(self.pose.flatten('C'))
    


    #Shutdown the Webcam
    def Shutdown(self):
        pygame.quit()
        #del(self._capture)




def main():

    port = 5555       
    t1 = RR.LocalTransport()
    t1.StartServerAsNodeName("cloth_rr")
    RRN.RegisterTransport(t1)

    t2 = RR.TcpTransport()
    t2.EnableNodeAnnounce()
    t2.StartServer(port)
    RRN.RegisterTransport(t2)
    
    obj=Cloth_impl()

    with open('cloth_rr.robdef', 'r') as f:
        service_def = f.read()
    
    RRN.RegisterServiceType(service_def)
    RRN.RegisterService("Cloth", "cloth_rr.Cloth", obj)
    
    input("Server started, press enter to quit...")

    obj.Shutdown()
    RRN.Shutdown()
    
#    
#    #Accept the names of the webcams and the nodename from command line
#            
#    parser = argparse.ArgumentParser(description="Azure Kinect Body Tracking Service")
#    #parser.add_argument("--camera-names",type=str,help="List of camera names separated with commas")
#    parser.add_argument("--nodename",type=str,default="AzureBodyTracking.Kinect",help="The NodeName to use")
#    parser.add_argument("--tcp-port",type=int,default=5555,help="The listen TCP port")
#    parser.add_argument("--wait-signal",action='store_const',const=True,default=False)
#    args = parser.parse_args()
#
#    #Initialize the webcam host root object
##    camera_names=[(0,"Left"),(1,"Right")]
##    if args.camera_names is not None:
##        camera_names_split=list(filter(None,args.camera_names.split(',')))
##        assert(len(camera_names_split) > 0)
##        camera_names = [(i,camera_names_split[i]) for i in range(len(camera_names_split))]
#        
#    
#    obj=Kinect_impl()
#    
#    with RR.ServerNodeSetup(args.nodename,args.tcp_port):
#
#        RRN.RegisterServiceTypeFromFile("AzureBodyTracking")
#        RRN.RegisterService("Kinect","AzureBodyTracking.Kinect",obj)
#    
#    
#        if args.wait_signal:  
#            #Wait for shutdown signal if running in service mode          
#            print("Press Ctrl-C to quit...")
#            import signal
#            signal.sigwait([signal.SIGTERM,signal.SIGINT])
#        else:
#            #Wait for the user to shutdown the service
#            if (sys.version_info > (3, 0)):
#                input("Server started, press enter to quit...")
#            else:
#                raw_input("Server started, press enter to quit...")
#    
#        #Shutdown
#        obj.Shutdown()    


if __name__ == '__main__':
    main()
