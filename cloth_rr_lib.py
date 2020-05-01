from OpenGL.GL import *
from OpenGL.GLU import *
import pygame
from pygame.locals import *
import sys, os, traceback
if sys.platform == 'win32' or sys.platform == 'win64':
    os.environ['SDL_VIDEO_CENTERED'] = '1'
from math import *
pygame.display.init()
pygame.font.init()
import numpy as np
import timeit


screen_size = [800,600]
multisample = 16
#icon = pygame.Surface((1,1)); icon.set_alpha(0); pygame.display.set_icon(icon)
pygame.display.set_caption("Cloth Demo")
if multisample:
    pygame.display.gl_set_attribute(GL_MULTISAMPLEBUFFERS,1)
    pygame.display.gl_set_attribute(GL_MULTISAMPLESAMPLES,multisample)
pygame.display.set_mode(screen_size,OPENGL|DOUBLEBUF)

#glEnable(GL_BLEND)
#glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)

#glEnable(GL_TEXTURE_2D)
#glTexEnvi(GL_TEXTURE_ENV,GL_TEXTURE_ENV_MODE,GL_MODULATE)
#glTexEnvi(GL_POINT_SPRITE,GL_COORD_REPLACE,GL_TRUE)

glHint(GL_PERSPECTIVE_CORRECTION_HINT,GL_NICEST)
glEnable(GL_DEPTH_TEST)

glPointSize(4)

def subtract(vec1,vec2):
    return [vec1[i]-vec2[i] for i in [0,1,2]]
def get_length(vec):
    return sum([vec[i]*vec[i] for i in [0,1,2]])**0.5

class Particle(object):
    def __init__(self,pos):
        self.pos = pos
        self.last_pos = list(self.pos)
        self.accel = [0.0,0.0,0.0]
        self.vel = [0.0,0.0,0.0]
        self.last_vel = [0.0,0.0,0.0]
        
        self.constrained = False
    def move(self,dt):
        #Don't move constrained particles
        if self.constrained: return
        #Move
        for i in [0,1,2]:
            #Verlet
            temp = 2*self.pos[i] - self.last_pos[i] + self.accel[i]*dt*dt
            self.last_pos[i] = self.pos[i]
            self.pos[i] = temp
            
#            if self.pos[i] < 0.0: self.pos[i] = 0.0
#            elif self.pos[i] > 1.0: self.pos[i] = 1.0
    def draw(self):
        glVertex3fv(self.pos)
class Edge(object):
    def __init__(self, p1,p2, tolerance=0.01):
        self.p1 = p1
        self.p2 = p2

        self.tolerance = tolerance
        
        self.rest_length = get_length(subtract(self.p2.pos,self.p1.pos))
        self.lower_length = self.rest_length*(1.0-self.tolerance)
        self.upper_length = self.rest_length*(1.0+self.tolerance)
        
    def constrain(self):
        vec = [self.p2.pos[i]-self.p1.pos[i] for i in [0,1,2]]
        length = get_length(vec)

        if   length > self.upper_length:
            target_length = self.upper_length
            strength = 1
        elif length < self.lower_length:
            target_length = self.lower_length
            strength = 1
        elif length > self.rest_length:
            target_length = self.rest_length
            strength = (length - self.rest_length) / ( 10*self.rest_length)
        elif length < self.rest_length:
            target_length = self.rest_length
            strength = (length - self.rest_length) / (-10*self.rest_length)
        else:
            return
        
#        print ('Test:', self.rest_length)
        movement_for_each = strength * (length - target_length) / 0.5#0.5#2.0

        for i in [0,1,2]:
            if not self.p1.constrained: self.p1.pos[i] += movement_for_each*vec[i]
            else: self.p1.vel[i] += movement_for_each*vec[i]
            if not self.p2.constrained: self.p2.pos[i] -= movement_for_each*vec[i]
            else: self.p2.vel[i] -= movement_for_each*vec[i]
            
            
class ClothCPU(object):
    def __init__(self, res):
        self.res = res

        corners = [
            [-1,-1],        [ 1,-1],

            [-1, 1],        [ 1, 1]
        ]
        edges = [
                    [ 0,-1],
            [-1, 0],        [ 1, 0],
                    [ 0, 1]
        ]
        self.rels = edges + corners
        for rel in self.rels:
            length = sum([rel[i]*rel[i] for i in [0,1]])**0.5
            rel.append(length/float(self.res))

        self.reset()
    def reset(self):
        self.particles = []
        for z in range(self.res):
            row = []
            for x in range(self.res):
                row.append(Particle([
                    float(x)/float(self.res-1),
                    1.0,
                    float(z)/float(self.res-1)
                ]))
            self.particles.append(row)
        self.particles[         0][         0].constrained = True
        self.particles[self.res-1][         0].constrained = True
        self.particles[         0][self.res-1].constrained = True
        self.particles[self.res-1][self.res-1].constrained = True        
        #self.particles[         0][self.res-1].constrained = True

        self.edges = []
        for z1 in range(self.res):
            for x1 in range(self.res):
                p1 = self.particles[z1][x1]
                for rel in self.rels:
                    x2 = x1 + rel[0]
                    z2 = z1 + rel[1]
                    if x2 < 0 or x2 >= self.res: continue
                    if z2 < 0 or z2 >= self.res: continue
                    p2 = self.particles[z2][x2]

                    found = False
                    for edge in self.edges:
                        if edge.p1 == p2:
                            found = True
                            break
                    if found: continue

                    self.edges.append(Edge(p1,p2))

    def constrain(self, n):
        for constraint_pass in range(n):
            for edge in self.edges:
                edge.constrain()
    def update(self,dt):
        #Gravity
        for row in self.particles:
            for particle in row:
                particle.accel = [0.0, gravity, 0.0]
        #Move everything
        for row in self.particles:
            for particle in row:
                particle.move(dt)
                
    def update_mouse(self,dt,mouse_rel):
        #Gravity
        for row in self.particles:
            for particle in row:
                particle.accel = [0.0, gravity, 0.0]
                
#        self.particles[         0][         0].constrained = False
#        self.particles[point_n-1][         0].constrained = False    

        self.particles[         0][         0].accel = [mouse_rel[0]/10.0, -mouse_rel[1]/10.0, 0.0]
        self.particles[ point_n-1][         0].accel = [mouse_rel[0]/10.0, -mouse_rel[1]/10.0, 0.0]  
        for i in [0,1,2]:
            self.particles[         0][         0].last_pos[i] = self.particles[         0][         0].pos[i]
            self.particles[ point_n-1][         0].last_pos[i] = self.particles[ point_n-1][         0].pos[i]
            self.particles[         0][         0].pos[i] = self.particles[         0][         0].pos[i]+self.particles[         0][         0].accel[i]*dt
            self.particles[ point_n-1][         0].pos[i] = self.particles[ point_n-1][         0].pos[i]+self.particles[ point_n-1][         0].accel[i]*dt                   
        #Move everything

        for row in self.particles:
            for particle in row:
                particle.move(dt)


    def draw(self):
        glBegin(GL_POINTS)
        for row in self.particles:
            for particle in row:
                particle.draw()
        glEnd()
    def draw_wireframe(self):
        glBegin(GL_LINES)
        for edge in self.edges:
            glVertex3fv(edge.p1.pos)
            glVertex3fv(edge.p2.pos)
        glEnd()
    def draw_mesh(self):
        for z in range(self.res-1):
            glBegin(GL_QUAD_STRIP)
            for x in range(self.res):
                glVertex3fv(self.particles[z  ][x].pos)
                glVertex3fv(self.particles[z+1][x].pos)
            glEnd()
    




gravity = -4.9#-9.80665
point_n = 11
cloth = ClothCPU(point_n)
target_fps = 30
dt = 1.0/float(target_fps)

camera_rot = [70,23]
camera_radius = 2.5
camera_center = [0.5,0.5,0.5]

def get_input():
    global camera_rot, camera_radius
    keys_pressed = pygame.key.get_pressed()
    mouse_buttons = pygame.mouse.get_pressed()
    mouse_rel = pygame.mouse.get_rel()
    for event in pygame.event.get():
        if   event.type == QUIT: return False
        elif event.type == KEYDOWN:
            if   event.key == K_ESCAPE: return False
            elif event.key == K_r: cloth.reset()
        elif event.type == MOUSEBUTTONDOWN:
            if   event.button == 4: camera_radius -= 0.5
            elif event.button == 5: camera_radius += 0.5
    if mouse_buttons[0]:
        #print (mouse_rel)
 
        
        cloth.constrain(3)
        cloth.update_mouse(dt,mouse_rel)
        
#        cloth.particles[         0][         0].constrained = True
#        cloth.particles[point_n-1][         0].constrained = True
        #camera_rot[0] += mouse_rel[0]
        #camera_rot[1] += mouse_rel[1]
    else:
        update(dt)

#    v1 = np.array(cloth.particles[         0][point_n-1].pos) - np.array(cloth.particles[         0][point_n-1].last_pos)
#    v2 = np.array(cloth.particles[point_n-1][point_n-1].pos) - np.array(cloth.particles[point_n-1][point_n-1].last_pos)
#    print ('V: ',v1,v2)
    
    for i in [0,1,2]:
        cloth.particles[         0][point_n-1].vel[i] += (cloth.particles[         0][point_n-1].pos[i] - cloth.particles[         0][point_n-1].last_pos[i])
        cloth.particles[point_n-1][point_n-1].vel[i] += (cloth.particles[point_n-1][point_n-1].pos[i] - cloth.particles[point_n-1][point_n-1].last_pos[i])        
        
        cloth.particles[         0][point_n-1].accel[i] = cloth.particles[         0][point_n-1].vel[i]-cloth.particles[         0][point_n-1].last_vel[i]
        cloth.particles[point_n-1][point_n-1].accel[i] = cloth.particles[point_n-1][point_n-1].vel[i]-cloth.particles[point_n-1][point_n-1].last_vel[i]
        
#    cloth.particles[        0][point_n-1].pos[2] = cloth.particles[        0][point_n-1].pos[2]+0.01*(-0.05-cloth.particles[        0][point_n-1].vel[2])
#    cloth.particles[point_n-1][point_n-1].pos[2] = cloth.particles[point_n-1][point_n-1].pos[2]+0.01*( 0.05-cloth.particles[point_n-1][point_n-1].vel[2])
#    cloth.particles[        0][point_n-1].last_pos[2] = cloth.particles[        0][point_n-1].pos[2]
#    cloth.particles[point_n-1][point_n-1].last_pos[2] = cloth.particles[point_n-1][point_n-1].pos[2]
        
    cloth.particles[         0][point_n-1].last_vel = cloth.particles[         0][point_n-1].vel
    cloth.particles[point_n-1][point_n-1].last_vel = cloth.particles[point_n-1][point_n-1].vel        
    cloth.particles[         0][point_n-1].vel = [0.0,0.0,0.0]
    cloth.particles[point_n-1][point_n-1].vel = [0.0,0.0,0.0]

    
    #print ("S: ",cloth.particles[         0][point_n-1].last_vel,cloth.particles[point_n-1][point_n-1].last_vel)
#    print ("Acc: ",cloth.particles[         0][point_n-1].accel,cloth.particles[point_n-1][point_n-1].accel)  
    #print ("Acc: ",cloth.particles[         0][point_n-1].accel,cloth.particles[point_n-1][point_n-1].accel) 
    return True

def update(dt):
    cloth.constrain(3)
    cloth.update(dt)
    
    
def draw():
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    
    glViewport(0,0,screen_size[0],screen_size[1])
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45,float(screen_size[0])/float(screen_size[1]), 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    camera_pos = [
        camera_center[0] + camera_radius*cos(radians(camera_rot[0]))*cos(radians(camera_rot[1])),
        camera_center[1] + camera_radius                            *sin(radians(camera_rot[1])),
        camera_center[2] + camera_radius*sin(radians(camera_rot[0]))*cos(radians(camera_rot[1]))
    ]
    gluLookAt(
        camera_pos[0],camera_pos[1],camera_pos[2],
        camera_center[0],camera_center[1],camera_center[2],
        0,1,0
    )

    cloth.draw()

    glColor3f(0,0.2,0)
    cloth.draw_wireframe()

    glColor3f(1,0,0)
    glBegin(GL_LINES)
    points = []
    for x in [0,1]:
        for y in [0,1]:
            for z in [0,1]:
                points.append([x,y,z])
    for p1 in points:
        for p2 in points:
            unequal = sum([int(p1[i]!=p2[i]) for i in [0,1,2]])
            if unequal == 1:
                glVertex3fv(p1)
                glVertex3fv(p2)
    glEnd()

    glColor3f(1,1,1)
    
    pygame.display.flip()
    
    
def main():
    t_all=[]
    clock = pygame.time.Clock()
    
    while True:
    #for i in range(1000):
        tic = timeit.default_timer()
        if not get_input(): break

        pos = []
        for x in range(point_n):
            for y in range(point_n):
                    pos.append(np.array(cloth.particles[x][y].pos))     
                    
        pos = np.array(pos)          
        print pos.flatten('C')   
#        return list(pos.flatten('C'))
        
        draw()
        clock.tick(target_fps)
        t_all.append(timeit.default_timer()-tic)
        
    #print (np.mean(t_all),np.std(t_all))    
    pygame.quit()
    
if __name__ == '__main__':
    try:
        main()
    except:
        traceback.print_exc()
        pygame.quit()
        input()
