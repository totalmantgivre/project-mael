import pygame
import math
import time

pygame.init()

WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

CELL_SIZE = 50
ROWS = HEIGHT // CELL_SIZE
COLS = WIDTH // CELL_SIZE


# TOWER

TOWER_TYPES = {
    0: {"type": "normal", "range": 140, "cooldown": 70, "damage": 2, "color": (200,200,255)},   # Archer
    1: {"type": "sniper", "range": 300, "cooldown": 333, "damage": 20, "color": (100,100,255)}, # Sniper
    2: {"type": "mage", "range": 110, "cooldown": 200, "damage": 1, "fire_duration": 180, "tick":0.025, "color": (255,100,100)},  #mage
    3: {"type": "bomb", "range": 125, "cooldown": 108*2, "damage": 2, "splash_radius":80, "color":(255,165,0)},   #bomber
    4: {"type": "warrior", "range": 40, "cooldown": 140, "damage": 10, "splash_radius":50, "color":(50,50,50)},   #warrior
    5: {"type": "shoot", "range": 140, "cooldown": 20, "damage": 0.6, "color":(10,250,50)},   #shooter
    6: {"type": "crossbowman", "range": 140, "cooldown": 70, "damage": 1, "color":(153,102,0)}   #bomber
}



# COST AND PV

TOWER_COST = {0:200,1:500,2:300,3:300,4:300,5:500,6:400}
money = 400
lives = 20


def reset_game():
    global money, lives 
    global enemies, towers
    global selected_tower, selected_tower_type
    global wave_manager

    money = 400
    lives = 20
    enemies.clear()
    towers.clear()
    selected_tower = None
    selected_tower_type = None
    wave_manager = WaveManager(waves_data)

def end_screen():
    run = True
    while run:
      screen.fill((0, 0, 0))
      text = font.render("u lost,skill issue,r to restart", True, (255, 255, 255))
      screen.blit(text, (50, 250))
      for event in pygame.event.get():
         if event.type == pygame.KEYDOWN:
             if event.key == pygame.K_r:
               reset_game()
               run = False
      pygame.display.flip()
      
def win_screen():
    run = True
    while run:
      screen.fill((0, 0, 0))
      text = font.render("you won yayyy,lmao i'm impressed if anyone actually finished this shit,r to restart", True, (255, 255, 255))
      screen.blit(text, (50, 250))
      for event in pygame.event.get():
         if event.type == pygame.KEYDOWN:
             if event.key == pygame.K_r:
               reset_game()
               run = False
      pygame.display.flip()
# ENNEMIES

class Enemy:
    def __init__(self, path, speed=0.8, hp=5, color=(255,0,0), reward=10, camo=False, damage=1):
        self.path = path
        self.index = 0
        self.x, self.y = self.path[self.index]
        self.speed = speed
        self.max_hp = hp            
        self.hp = hp
        self.color = color
        self.reward = reward
        self.fire_timer = 0
        self.fire_damage = 0
        self.camo = camo
        self.damage = damage

    def update(self):
        if self.index < len(self.path) - 1:
            tx, ty = self.path[self.index + 1]
            dx, dy = tx - self.x, ty - self.y
            dist = math.hypot(dx, dy)
            if dist < self.speed:
                self.index += 1
            else:
                self.x += self.speed * dx / dist
                self.y += self.speed * dy / dist

    def draw(self, surf):
        radius=10
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), radius)
        hp_ratio = self.hp / self.max_hp
        if hp_ratio > 0.66: bar_color=(0,255,0)
        elif hp_ratio>0.33: bar_color=(255,165,0)
        else: bar_color=(255,0,0)
        bar_width, bar_height, offset_y = 30,5,-20
        pygame.draw.rect(surf,(0,0,0),(int(self.x-bar_width/2),int(self.y+offset_y),bar_width,bar_height))
        pygame.draw.rect(surf,bar_color,(int(self.x-bar_width/2),int(self.y+offset_y),int(bar_width*hp_ratio),bar_height))


# BULLETS

class Projectile:
    def __init__(self, x, y, target, speed=5, damage=1,fire=False, pierce=False, kind="normal", splash_radius=0, fire_duration=0):
        self.x = x
        self.y = y
        self.target = target
        self.speed = speed
        self.damage = damage
        self.fire = fire
        self.pierce = pierce
        self.kind = kind
        self.alive = True
        self.splash_radius = splash_radius
        self.fire_duration = fire_duration
        self.hit_enemies = set()
        # Direction toward the target when fired
        dx = target.x - x
        dy = target.y - y
        dist = math.hypot(dx, dy)
        if dist != 0:
            self.dx = dx / dist
            self.dy = dy / dist
        else:
            self.dx = 1
            self.dy = 0
    def hit_enemy(self, enemy):
        if enemy in self.hit_enemies:
            return
        self.hit_enemies.add(enemy)
        enemy.hp -= self.damage
        if self.fire:
            enemy.fire_timer = max(enemy.fire_timer, self.fire_duration)
            enemy.fire_damage = self.damage
        if self.splash_radius > 0:
            for e in enemies:
                if e != enemy and e not in self.hit_enemies:
                    if math.hypot(
                        e.x - enemy.x,
                        e.y - enemy.y
                    ) <= self.splash_radius:

                        e.hp -= self.damage
                        self.hit_enemies.add(e)
    def update(self):
        if not self.alive:
            return
        if not self.pierce:
        if self.target in enemies and self.target.hp > 0:
               dx = self.target.x - self.x
               dy = self.target.y - self.y
               dist = math.hypot(dx, dy)

               if dist != 0:
                   self.dx = dx / dist
                   self.dy = dy / dist

           self.x += self.dx * self.speed
           self.y += self.dy * self.speed

        for enemy in enemies:
            if enemy in self.hit_enemies:
                continue

            if enemy.hp <= 0:
                continue
    
            distance = math.hypot(
                enemy.x - self.x,
                enemy.y - self.y
            )

            if distance <= 15:
                self.hit_enemy(enemy)

                if not self.pierce:
                    self.alive = False
                    break

        if (self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT):
            self.alive = False


    def draw(self,surf):
        if self.kind=="normal":
            pygame.draw.line(surf,(0,255,0),(self.x,self.y),(self.x-3,self.y-3),6)
        elif self.kind=="mage":
            pygame.draw.circle(surf,(255,0,0),(int(self.x),int(self.y)),6)
        elif self.kind=="sniper":
            pygame.draw.circle(surf,(0,0,255),(int(self.x),int(self.y)),5)
        elif self.kind=="bomb":
            pygame.draw.circle(surf,(255,165,0),(int(self.x),int(self.y)),8)
        elif self.kind=="warrior":
            pygame.draw.circle(surf,(50,50,50),(int(self.x),int(self.y)),6)
        elif self.kind=="shoot":
            pygame.draw.circle(surf,(10,255,50),(int(self.x),int(self.y)),7)
        elif self.kind == "crossbowman": 
             pygame.draw.circle(surf,(153,102,0),(int(self.x),int(self.y)),7)
# TOWERS

class Tower:
    def __init__(self,x,y,tower_type):
        self.x,self.y = x,y
        self.type = tower_type
        stats = TOWER_TYPES[tower_type]
        self.kind = stats["type"]
        self.projectiles=[]
        self.timer=0
        self.targeting="closest"
        self.current_target = None
        self.level = 1
        self.upgrade_cost = 100 * (self.level ** 1.5)
        self.range = stats.get("range",0)
        self.cooldown = stats.get("cooldown",0)
        self.damage = stats.get("damage",0)
        self.total_spent = TOWER_COST[tower_type]  #sell stuff idk
        if self.kind=="mage":
            self.fire_duration = stats["fire_duration"] + (20 * self.level - 20)
            self.tick = stats["tick"]
        if self.kind=="bomb":
            self.splash_radius = stats["splash_radius"] + (10 * self.level - 10)
   
    def upgrade(self):
        global money
        if (self.level >= 4 and wave_manager.next_wave_id <= 11) or money < self.upgrade_cost or self.level >= 6:
           return False
        money -= self.upgrade_cost
        self.total_spent += self.upgrade_cost
        self.level += 1
        if self.kind=="normal":
            self.upgrade_cost = int(self.upgrade_cost*1.5)
            self.damage += 1.33
            if self.range: self.range += 20
            if self.cooldown: self.cooldown = max(1,int(self.cooldown*1))
        elif self.kind=="sniper":
            self.upgrade_cost = int(self.upgrade_cost*3)
            self.damage *= 2
            if self.range: self.range += 100
        elif self.kind=="bomb":
            self.upgrade_cost = int(self.upgrade_cost * 2)
            self.damage +=1
            if self.range: self.range += 10
            if self.cooldown: self.cooldown = max(1,int(self.cooldown*0.9))
        elif self.kind=="mage":
            self.upgrade_cost = int(self.upgrade_cost * 2)
            self.damage *= 1.3
            self.fire_duration += 40
            if self.range: self.range += 30
            if self.cooldown: self.cooldown = max(1,int(self.cooldown*1))
        elif self.kind=="warrior":
            self.upgrade_cost = int(self.upgrade_cost * 2)
            if self.range: self.range += 10
            self.damage += 5
            if self.cooldown: self.cooldown = max(1,int(self.cooldown*0.9))
        elif self.kind=="shoot":
            self.upgrade_cost = int(self.upgrade_cost * 3)
            self.damage += 0.3
            if self.cooldown: self.cooldown = max(1,int(self.cooldown*0.5))
            if self.range: self.range += 30

        return True

    def change_targeting(self):
        options = ["closest","first","strong"]
        idx = options.index(self.targeting)
        self.targeting = options[(idx+1)%3]

    def shoot(self,enemies):
        if self.timer>0:
            self.timer-=1
            return
        self.current_target = None
        in_range = [e for e in enemies if math.hypot(e.x-self.x,e.y-self.y)<=self.range]
        if self.kind in ["normal","mage"]:
            in_range = [e for e in in_range if not e.camo]
        if not in_range: return
        if self.targeting=="closest":
            target=min(in_range,key=lambda e:math.hypot(e.x-self.x,e.y-self.y))
        elif self.targeting=="first":
            target=max(in_range,key=lambda e:e.index)
        elif self.targeting=="strong":
            target=max(in_range,key=lambda e:e.hp)
        self.current_target = target
        dmg=self.damage
        fire=False
        kind=self.kind
        if self.kind=="mage":
            fire=True
            dmg=self.tick
        pierce=self.kind == "crossbowman"
        splash=getattr(self,"splash_radius",0)
       
        projectile_speed = 5
        if self.kind == "sniper":
            projectile_speed = 15
        elif self.kind == "shoot":
            projectile_speed = 8
        elif self.kind == "crossbowman":
            projectile_speed = 7
        elif self.kind == "mage":
            projectile_speed = 6

        self.projectiles.append(Projectile(self.x,self.y,target,damage=dmg,fire=fire,pierce=pierce,kind=kind,splash_radius=splash,fire_duration=self.fire_duration if self.kind == "mage" else 0))
        self.timer=self.cooldown

    def update_projectiles(self):
        for p in self.projectiles[:]:
            p.update()
            if not p.alive:
                self.projectiles.remove(p)

    def draw(self,surf):
        color = TOWER_TYPES[self.type]["color"]
        pygame.draw.circle(surf,color,(self.x,self.y),20)
        pygame.draw.circle(surf,(255,255,255),(self.x,self.y),self.range,1)
        for p in self.projectiles:
            p.draw(surf)
        font = pygame.font.SysFont(None, 20)
        txt = font.render(self.targeting.capitalize(), True, (255, 255, 0))
        surf.blit(txt, (self.x - txt.get_width() // 2, self.y - 30))


# PATH

path=[]
def P(c,r):
    return (c*CELL_SIZE+CELL_SIZE//2,r*CELL_SIZE+CELL_SIZE//2)
path+=[P(0,6),P(4,6),P(4,3),P(8,3),P(8,8),P(2,8),P(2,2),P(10,2),P(10,10),P(14,10),P(14,4),P(18,4),P(18,7),P(21,7)]

def draw_rounded_path(surf,path,width):
    if len(path)<2: return
    radius=width//2
    for i in range(len(path)-1):
        x1,y1=path[i]; x2,y2=path[i+1]
        dx,dy=x2-x1,y2-y1
        length=math.hypot(dx,dy)
        if length==0: continue
        nx,ny=-dy/length,dx/length
        points=[(x1+nx*radius,y1+ny*radius),(x2+nx*radius,y2+ny*radius),
                (x2-nx*radius,y2-ny*radius),(x1-nx*radius,y1-ny*radius)]
        pygame.draw.polygon(surf,(100,100,100),points)
    for x,y in path:
        pygame.draw.circle(surf,(100,100,100),(int(x),int(y)),radius)

def is_on_path(px,py):
    for i in range(len(path)-1):
        x1,y1=path[i]; x2,y2=path[i+1]
        AB=(x2-x1,y2-y1); AP=(px-x1,py-y1)
        ab2=AB[0]**2+AB[1]**2
        if ab2==0: continue
        t=max(0,min(1,(AP[0]*AB[0]+AP[1]*AB[1])/ab2))
        closest=(x1+AB[0]*t,y1+AB[1]*t)
        if math.hypot(px-closest[0],py-closest[1])<CELL_SIZE/2: return True
    return False


# WAVES

waves_data = [
    [("red",10)],
    [("red",20),("purple",5)], #2
    [("purple",5),("red",15),("purple",5),("yellow",3),("red",15),("yellow",5)], #3
    [("purple",5),("red",20),("gem",1),("red",10)], #4
    [("purple",5),("gem",1),("red",10),("purple",20)], #5
    [("yellow",2),("red",10),("yellow",10),("purple",5),("black",1)], #6
    [("red",15),("green",10),("gem",1),("yellow",20),("purple",10)],
    [("red",25),("black",1),("yellow",20),("purple",15)],
    [("red",35),("gem",1),("black",2)], #9
    [("yellow",25),("black",1),("green",10),("red",30)],
    [("purple",12),("gem",1),("yellow",25),("black",5)], #11
    [("black",3),("green",15),("black",3),("purple",12),("yellow",25),("black",5)], #12
    [("black",3),("red",40),("purple",20),("black",3),("yellow",35),("black",10),("gem",1),("god",1)], #13
    [("elite red",10),("black",10),("elite red",10),("black",10),("elite red",10)], #14
    [("elite red",5),("elite yellow",15),("elite purple",5),("elite purple",5),("elite red",5),("elite purple",5),("elite red",5),("black",3),("elite red",15)], #15
    [("black",1),("elite red",20),("elite green",10),("elite purple",15),("elite green",5),("elite black",1),("elite green",10)], #16
    [("elite purple",2),("elite yellow",5),("elite red",5),("elite purple",2),("elite yellow",5),("elite red",5),("elite purple",2),("elite yellow",5),("elite red",5),("elite purple",2),("elite yellow",5),("elite red",5),("elite purple",2),("elite yellow",5),("elite red",5),("elite black",1)], #17
    [("elite red",30),("elite yellow",15),("elite purple",15),("elite yellow",15),("black",20)], #18
    [("elite red",15),("elite green",10),("elite yellow",20),("elite green",10),("elite purple",20),], #19
    [("elite red",25),("elite yellow",20),("elite purple",15),("elite red",25),("elite yellow",20),("elite purple",15),("elite red",25),("elite yellow",20),("elite purple",15),("elite black",5)], #20
    [("elite purple",50),("elite black",10)],
    [("elite black",3),("elite yellow",5),("elite black",3),("elite yellow",5),("elite black",3),("elite yellow",5),("elite black",3),("elite yellow",5),("elite black",3),("elite yellow",5),("elite black",3),("elite yellow",5),("elite black",3),("elite yellow",5)], #22
    [("black",20),("elite black",3),("black",20),("elite red",50)],
    [("elite green",10),("elite yellow",15),("black",30),("elite yellow",15),("elite black",5),("elite yellow",5),("elite black",3),("elite yellow",5),("elite black",3),("elite purple",50)], #24
    [("elite purple",10),("black",25),("elite purple",10),("elite black",25),("black",50),("elite black",25),("elite god",1)] #
    ]
class Wave:
    def __init__(self,enemy_list,interval=80):
        self.enemy_list=enemy_list[:]
        self.interval=interval
        self.spawn_timer=0
        self.spawn_index=0
        self.total=sum(q for _,q in self.enemy_list)
        self.finished=False

    def update(self,enemies,path):
        global money
        if self.finished: return
        self.spawn_timer+=1
        if self.spawn_timer>=self.interval and self.spawn_index<self.total:
            self.spawn_timer=0
            counter=0
            for kind,qty in self.enemy_list:
                if self.spawn_index<counter+qty:
                    enemy_type=kind
                    break
                counter+=qty
            self.spawn_index+=1
            if enemy_type=="red":
                enemies.append(Enemy(path, speed=0.9, hp=5, color=(255,0,0), reward=10, damage=1))
            elif enemy_type=="purple":
                enemies.append(Enemy(path, speed=0.5, hp=25, color=(128,0,128), reward=15, damage=3))
            elif enemy_type=="yellow":
                enemies.append(Enemy(path, speed=2.0, hp=3, color=(255,255,0), reward=5, damage=1))
            elif enemy_type=="black":
                enemies.append(Enemy(path, speed=0.75, hp=200, color=(50,50,50), reward=30, damage=10))
            elif enemy_type=="green":
                enemies.append(Enemy(path, speed=1.0, hp=10, color=(0,255,0), reward=10, camo=True, damage=2))
            elif enemy_type=="god":
                enemies.append(Enemy(path, speed=0.5, hp=1000, color=(255,255,255), reward=1000, damage=19))
            elif enemy_type=="greml":
                enemies.append(Enemy(path, speed=2, hp=1, color=(0,255,128), reward=1, damage=1))
            elif enemy_type=="gem":
                enemies.append(Enemy(path, speed=0.9, hp=250, color=(170,255,255), reward=200, damage=0))
            elif enemy_type=="elite red":
                enemies.append(Enemy(path, speed=1.3, hp=40, color=(104,10,10), reward=10, damage=2))
            elif enemy_type=="elite purple":
                enemies.append(Enemy(path, speed=0.75, hp=150, color=(60,40,178), reward=20, damage=5))
            elif enemy_type=="elite yellow":
                enemies.append(Enemy(path, speed=5.0, hp=10, color=(255,192,82), reward=5, damage=2))
            elif enemy_type=="elite black":
                enemies.append(Enemy(path, speed=1.0, hp=800, color=(0,0,0), reward=30, damage=10))
            elif enemy_type=="elite green":
                enemies.append(Enemy(path, speed=1.5, hp=10, color=(70,125,60), reward=10, camo=True, damage=2))
            elif enemy_type=="elite god":
                enemies.append(Enemy(path, speed=1, hp=100000, color=(255,100,100), reward=10000, damage=99))
            elif enemy_type=="elite gem":
                enemies.append(Enemy(path, speed=1.3, hp=1000, color=(170,255,255), reward=1000, damage=0))
        if self.spawn_index>=self.total:
            self.finished=True

class WaveManager:
    def __init__(self,waves_data):
        self.waves_data=waves_data[:]
        self.active_waves=[]
        self.next_wave_id=0
        self.last_wave_time=-100

    def launch_next_wave(self):
        global money
        if time.time()-self.last_wave_time<3: return #time wave delay
        if self.next_wave_id<len(self.waves_data):
            data=self.waves_data[self.next_wave_id]
            self.active_waves.append(Wave(data))
            self.next_wave_id+=1
            if self.next_wave_id<=13:
                money+=50
            elif self.next_wave_id>13:
                money+=100
            self.last_wave_time=time.time()
        if (wave_manager.next_wave_id >= len(waves_data) and not wave_manager.active_waves and not enemies):
            win_screen()
    def update(self,enemies,path):
        for w in self.active_waves: w.update(enemies,path)
        self.active_waves=[w for w in self.active_waves if not w.finished]

wave_manager=WaveManager(waves_data)


# UI

selected_tower_type=None
selected_tower=None
BUTTON_WIDTH, BUTTON_HEIGHT = 120,50
buttons=[]
for i in range(7):
    bx=10+i*(BUTTON_WIDTH+10)
    by=HEIGHT-BUTTON_HEIGHT-10
    buttons.append(pygame.Rect(bx,by,BUTTON_WIDTH,BUTTON_HEIGHT))
wave_button = pygame.Rect(WIDTH-150,HEIGHT-60,140,50)
upgrade_button = pygame.Rect(WIDTH-150,HEIGHT-120,140,50)
sell_button = pygame.Rect(WIDTH-150, HEIGHT-180, 140, 50)  # sell

enemies=[]
towers=[]


# MAIN LOOP

running=True
while running:
    for event in pygame.event.get():
        if event.type==pygame.QUIT: running=False
        elif event.type==pygame.MOUSEBUTTONDOWN and event.button in [1,3]:
            mx,my=event.pos
            # wave button
            if wave_button.collidepoint(mx,my) and event.button==1:
                wave_manager.launch_next_wave()
                continue
            # tower button
            tower_selected=False
            for i,rect in enumerate(buttons):
                if rect.collidepoint(mx,my) and event.button==1:
                    selected_tower_type=i
                    selected_tower=None
                    tower_selected=True
                    break
            if tower_selected: continue
            # upgrade
            if selected_tower and upgrade_button.collidepoint(mx,my) and event.button==1:
                selected_tower.upgrade()
                continue
            # sell
            if selected_tower and sell_button.collidepoint(mx,my) and event.button==1:
                refund = int(selected_tower.total_spent * 0.7)
                money += refund
                towers.remove(selected_tower)
                selected_tower=None
                continue
            # clic
            clicked_on_tower=False
            for t in towers:
                if math.hypot(mx-t.x,my-t.y)<25:
                    clicked_on_tower=True
                    selected_tower=t
                    if event.button==3:
                        t.change_targeting()
                    break
            if clicked_on_tower: continue
            # place
            if selected_tower_type is not None and money>=TOWER_COST[selected_tower_type]:
                col,row=mx//CELL_SIZE,my//CELL_SIZE
                tx=col*CELL_SIZE+CELL_SIZE//2
                ty=row*CELL_SIZE+CELL_SIZE//2
                ttype=TOWER_TYPES[selected_tower_type]["type"]
                if not any(math.hypot(t.x-tx,t.y-ty)<CELL_SIZE/2 for t in towers):
                    towers.append(Tower(tx,ty,selected_tower_type))
                    money-=TOWER_COST[selected_tower_type]

    wave_manager.update(enemies,path)

    for e in enemies[:]:
        e.update()
        if e.fire_timer>0:
            e.hp-= e.fire_damage
            e.fire_timer-=1
        if e.hp<=0:
            money+=e.reward
            enemies.remove(e)
        elif e.index>=len(path)-1:
            screen.fill((255, 0, 0))
            lives-=e.damage
            if lives<1:
                end_screen()
                break
            enemies.remove(e)

    for t in towers:
        t.shoot(enemies)
        t.update_projectiles()

    # DRAW
    screen.fill((30,30,30))
    for r in range(ROWS):
        for c in range(COLS):
            pygame.draw.rect(screen,(50,50,50),(c*CELL_SIZE,r*CELL_SIZE,CELL_SIZE,CELL_SIZE),1)
    draw_rounded_path(screen,path,CELL_SIZE)
    for e in enemies: e.draw(screen)
    for t in towers: t.draw(screen)
    font = pygame.font.SysFont(None,24)
    # tower button
    for i,rect in enumerate(buttons):
        color=(80,80,80) if selected_tower_type!=i else (150,150,255)
        pygame.draw.rect(screen,color,rect)
        pygame.draw.rect(screen,(255,255,255),rect,2)
        txt=font.render(f"{TOWER_TYPES[i]['type']} (${TOWER_COST[i]})",True,(255,255,255))
        screen.blit(txt,(rect.x+5,rect.y+15))
    # upgrade
    pygame.draw.rect(screen,(80,80,80),upgrade_button)
    pygame.draw.rect(screen,(255,255,255),upgrade_button,2)
    txt=font.render(f"Upgrade (${selected_tower.upgrade_cost if selected_tower else '-'})",True,(255,255,255))
    screen.blit(txt,(upgrade_button.x+5,upgrade_button.y+15))
    # sell
    pygame.draw.rect(screen,(80,80,80),sell_button)
    pygame.draw.rect(screen,(255,255,255),sell_button,2)
    txt=font.render(f"Sell (${int(selected_tower.total_spent*0.7) if selected_tower else '-'})", True,(255,255,255))
    screen.blit(txt,(sell_button.x+5,sell_button.y+15))
    # wave
    pygame.draw.rect(screen,(80,80,80),wave_button)
    pygame.draw.rect(screen,(255,255,255),wave_button,2)
    if wave_manager.next_wave_id<=13: 
        txt=font.render("Next Wave (+$50)",True,(255,255,255))
    if wave_manager.next_wave_id>13:
        txt=font.render("Next Wave (+$100)",True,(255,255,255))
    screen.blit(txt,(wave_button.x+5,wave_button.y+15))
    # money/lives
    txt = font.render(f"Wave: {wave_manager.next_wave_id}  Money: ${money}  Lives: {lives}", True, (255, 255, 0))
    screen.blit(txt, (WIDTH - txt.get_width() - 10, 10))



    pygame.display.flip()
    clock.tick(240)

pygame.quit()
