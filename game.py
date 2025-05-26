from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import math

# Game state variables
player_pos = [0, 0, 0]  # Player position (x, y, z)
player_angle = 0  # Player facing direction
gun_angle = 0  # Gun rotation relative to player
player_life = 5  # Player lives
score = 0  # Game score
bullets_missed = 0  # Missed bullets count
game_over = False  # Game over flag

# Movement properties
move_speed = 10  # Movement speed
rot_speed = 5    # Rotation speed

# Gun properties
gun_length = 60  # Length of the gun barrel

# Bullet properties
bullets = []  # List of active bullets
bullet_speed = 12  # Speed of bullets
bullet_size = 10  # Size of bullet cubes

# Enemy properties
enemies = []  # List of enemies
num_enemies = 5  # Number of enemies
enemy_speed = 0.15  # Base speed of enemies (reduced from 0.3 to make enemies much slower)
enemy_base_size = 30  # Base size of enemies
enemy_pulse = 0  # For size pulsing effect

# Camera properties
camera_angle = 45  # Camera rotation around player
camera_height = 400  # Camera height
camera_distance = 600  # Camera distance from player
first_person = False  # First-person view flag

# Cheat mode flags
cheat_mode = False  # Auto-aim and fire

# Grid properties
GRID_LENGTH = 600  # Length of grid lines
BOUNDARY_HEIGHT = 50  # Height of boundary walls


def init_game():
    """Initialize or reset the game state"""
    global player_pos, gun_angle, player_life, score, bullets_missed, game_over
    global bullets, enemies

    player_pos = [0, 0, 0]
    gun_angle = 0
    player_life = 5
    score = 0
    bullets_missed = 0
    game_over = False
    bullets = []

    # Initialize enemies
    enemies.clear()
    for _ in range(num_enemies):
        spawn_enemy()


def spawn_enemy():
    """Spawn an enemy at a random position on the grid"""
    x = random.uniform(-GRID_LENGTH + 50, GRID_LENGTH - 50)
    y = random.uniform(-GRID_LENGTH + 50, GRID_LENGTH - 50)
    # Format: [x, y, z, size, angle]
    enemies.append([x, y, 0, enemy_base_size, random.uniform(0, 360)])


def draw_player():
    """Draw the player character according to the diagram"""
    if not first_person:  # Only draw player model in third person view
        glPushMatrix()
        glTranslatef(*player_pos)

        # Body (rectangular prism)
        glColor3f(0.7, 0.7, 0.7)  # Gray color
        glutSolidCube(20)  # Simple body cube

        # Head (sphere)
        glColor3f(0.8, 0.8, 0.8)
        glPushMatrix()
        glTranslatef(0, 0, 40)  # Place on top of body
        glutSolidSphere(10, 16, 16)
        glPopMatrix()

        # Gun assembly
        glPushMatrix()
        glRotatef(gun_angle, 0, 0, 1)  # Rotate gun
        glTranslatef(0, 0, 30)  # Height of gun placement

        # Simple gun shape
        glColor3f(0.3, 0.3, 0.3)  # Dark gray
        glutSolidCube(10)  # Gun base
        glTranslatef(30, 0, 0)  # Move to gun tip
        glutSolidCube(5)  # Gun tip

        glPopMatrix()  # Gun assembly
        glPopMatrix()  # Player
    else:
        # Draw first-person gun model
        glPushMatrix()
        # Position gun in front of camera
        glTranslatef(player_pos[0], player_pos[1], player_pos[2] + 20)
        glRotatef(gun_angle, 0, 0, 1)
        
        # Simple gun model for first person
        glColor3f(0.4, 0.4, 0.4)  # Dark gray
        glTranslatef(20, 0, 0)
        glutSolidCube(10)  # Gun base
        glTranslatef(20, 0, 0)
        glutSolidCube(5)  # Gun tip
        
        glPopMatrix()


def draw_enemies():
    """Draw all enemies as red spheres with black spheres on top"""
    global enemy_pulse
    enemy_pulse = (enemy_pulse + 2) % 360
    pulse_factor = 0.25 * math.sin(math.radians(enemy_pulse)) + 1

    for enemy in enemies:
        glPushMatrix()
        glTranslatef(enemy[0], enemy[1], enemy[2])

        # Main body (red sphere)
        glColor3f(1.0, 0.0, 0.0)  # Bright red
        glutSolidSphere(enemy[3] * pulse_factor, 32, 32)

        # Head (black sphere)
        glColor3f(0.0, 0.0, 0.0)  # Black
        glTranslatef(0, 0, enemy[3] * 0.8)  # Move up relative to main body
        glutSolidSphere(enemy[3] * 0.4, 32, 32)  # Smaller sphere for head

        glPopMatrix()


def draw_grid():
    """Draw the game grid with checkerboard pattern"""
    # Grid surface
    glBegin(GL_QUADS)
    
    # Draw checkerboard pattern
    square_size = 50  # Size of each square
    rows = GRID_LENGTH * 2 // square_size
    cols = GRID_LENGTH * 2 // square_size
    
    for row in range(rows):
        for col in range(cols):
            x = col * square_size - GRID_LENGTH
            y = row * square_size - GRID_LENGTH
            
            # Alternate colors based on position
            if (row + col) % 2 == 0:
                glColor3f(1, 1, 1)  # White
            else:
                glColor3f(0.7, 0.5, 0.95)  # Purple
                
            glVertex3f(x, y, 0)
            glVertex3f(x + square_size, y, 0)
            glVertex3f(x + square_size, y + square_size, 0)
            glVertex3f(x, y + square_size, 0)
    
    glEnd()

    # Draw colored boundaries
    glColor3f(0, 0, 1)  # Blue for left boundary
    glBegin(GL_QUADS)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, BOUNDARY_HEIGHT)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, BOUNDARY_HEIGHT)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0)
    glEnd()

    glColor3f(0, 1, 0)  # Green for right boundary
    glBegin(GL_QUADS)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, BOUNDARY_HEIGHT)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, BOUNDARY_HEIGHT)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, 0)
    glEnd()


def update_movement():
    """Update bullet and enemy positions"""
    global bullets, bullets_missed, score, player_life, game_over

    # Update bullets
    for bullet in bullets[:]:
        # Move bullet in its stored direction
        angle = math.radians(bullet['angle'])
        bullet['pos'][0] += bullet_speed * math.cos(angle)
        bullet['pos'][1] += bullet_speed * math.sin(angle)

        # Boundary check
        if not (-GRID_LENGTH < bullet['pos'][0] < GRID_LENGTH and
                -GRID_LENGTH < bullet['pos'][1] < GRID_LENGTH):
            bullets.remove(bullet)
            bullets_missed += 1
            if bullets_missed >= 10:
                game_over = True

    # Update enemies
    for enemy in enemies[:]:
        # Calculate direction to player
        dx = player_pos[0] - enemy[0]
        dy = player_pos[1] - enemy[1]
        dist = math.hypot(dx, dy)

        if dist > 0:
            enemy[0] += (dx / dist) * enemy_speed
            enemy[1] += (dy / dist) * enemy_speed

        # Collision with player
        if dist < 40 and not game_over:
            player_life -= 1
            if player_life <= 0:
                game_over = True
            enemy[0], enemy[1] = random.uniform(-GRID_LENGTH + 50, GRID_LENGTH - 50), random.uniform(-GRID_LENGTH + 50,
                                                                                                     GRID_LENGTH - 50)

    # Check bullet-enemy collisions
    for bullet in bullets[:]:
        for enemy in enemies[:]:
            if math.hypot(bullet['pos'][0] - enemy[0], bullet['pos'][1] - enemy[1]) < enemy[3] + bullet_size/2:
                bullets.remove(bullet)
                enemies.remove(enemy)
                spawn_enemy()
                score += 5
                break


def keyboardListener(key, x, y):
    """Handle keyboard inputs"""
    global player_pos, gun_angle, player_angle, cheat_mode, game_over
    key = key.decode('utf-8').lower()

    if game_over and key == 'r':
        init_game()
        return

    # Move forward (W)
    if key == 'w':
        angle = math.radians(gun_angle)
        player_pos[0] += move_speed * math.cos(angle)
        player_pos[1] += move_speed * math.sin(angle)

    # Move backward (S)
    elif key == 's':
        angle = math.radians(gun_angle)
        player_pos[0] -= move_speed * math.cos(angle)
        player_pos[1] -= move_speed * math.sin(angle)

    # Rotate gun (A/D)
    elif key == 'a':  # Rotate counterclockwise (left)
        gun_angle = (gun_angle + rot_speed) % 360
    elif key == 'd':  # Rotate clockwise (right)
        gun_angle = (gun_angle - rot_speed) % 360

    elif key == 'c':  # Toggle cheat mode
        cheat_mode = not cheat_mode

    # Keep player within bounds
    player_pos[0] = max(-GRID_LENGTH + 30, min(GRID_LENGTH - 30, player_pos[0]))
    player_pos[1] = max(-GRID_LENGTH + 30, min(GRID_LENGTH - 30, player_pos[1]))


def specialKeyListener(key, x, y):
    """Handle camera controls"""
    global camera_angle, camera_height
    if key == GLUT_KEY_UP:
        camera_height = min(800, camera_height + 20)
    elif key == GLUT_KEY_DOWN:
        camera_height = max(100, camera_height - 20)
    elif key == GLUT_KEY_LEFT:
        camera_angle = (camera_angle + 5) % 360
    elif key == GLUT_KEY_RIGHT:
        camera_angle = (camera_angle - 5) % 360


def mouseListener(button, state, x, y):
    """Handle mouse inputs"""
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and not game_over:
        # Calculate bullet direction based on gun angle
        angle = math.radians(gun_angle)
        
        # Calculate bullet starting position at the tip of the gun
        start_x = player_pos[0] + gun_length * math.cos(angle)
        start_y = player_pos[1] + gun_length * math.sin(angle)
        start_z = player_pos[2] + 30  # Height of the gun
        
        # Create bullet with position and angle
        bullets.append({
            'pos': [start_x, start_y, start_z],
            'angle': gun_angle
        })
    
    elif button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        global first_person
        first_person = not first_person


def setupCamera():
    """Configure camera based on current mode"""
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, 1.25, 1, 2000)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if first_person:
        # First-person view from player's eye level
        eye_height = 40  # Height of player's eyes
        # Position camera at player position plus eye height
        gluLookAt(player_pos[0], player_pos[1], player_pos[2] + eye_height,  # Camera position
                  player_pos[0] + math.cos(math.radians(gun_angle)),  # Look at point x
                  player_pos[1] + math.sin(math.radians(gun_angle)),  # Look at point y
                  player_pos[2] + eye_height,  # Look at point z (same height as camera)
                  0, 0, 1)  # Up vector
    else:
        # Third-person orbiting view
        cam_x = player_pos[0] + camera_distance * math.sin(math.radians(camera_angle))
        cam_y = player_pos[1] + camera_distance * math.cos(math.radians(camera_angle))
        gluLookAt(cam_x, cam_y, camera_height,
                  player_pos[0], player_pos[1], 40,
                  0, 0, 1)


def idle():
    """Handle automatic updates"""
    global gun_angle
    
    if cheat_mode and not game_over:
        # Find nearest enemy
        nearest_enemy = None
        min_dist = float('inf')
        for enemy in enemies:
            dx = enemy[0] - player_pos[0]
            dy = enemy[1] - player_pos[1]
            dist = math.hypot(dx, dy)
            if dist < min_dist:
                min_dist = dist
                nearest_enemy = enemy
        
        if nearest_enemy:
            # Calculate angle to nearest enemy
            dx = nearest_enemy[0] - player_pos[0]
            dy = nearest_enemy[1] - player_pos[1]
            target_angle = math.degrees(math.atan2(dy, dx))
            # Normalize target angle to 0-360 range
            target_angle = target_angle % 360
            
            # Smoothly rotate gun towards target
            angle_diff = (target_angle - gun_angle) % 360
            if angle_diff > 180:
                angle_diff -= 360
            gun_angle = (gun_angle + min(max(angle_diff, -6), 6)) % 360
            
            # Auto-fire when pointing at enemy (within 10 degrees)
            if abs(angle_diff) < 10 and random.random() < 0.1:  # Normal fire rate
                angle = math.radians(gun_angle)
                bullets.append({
                    'pos': [
                        player_pos[0] + gun_length * math.cos(angle),
                        player_pos[1] + gun_length * math.sin(angle),
                        20
                    ],
                    'angle': gun_angle
                })

    update_movement()
    glutPostRedisplay()


def draw_text(x, y, text):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()

    # Set up an orthographic projection that matches window coordinates
    gluOrtho2D(0, 1000, 0, 800)  # left, right, bottom, top

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Draw text at (x, y) in screen coordinates
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    # Restore original projection and modelview matrices
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def showScreen():
    """Main rendering function"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)

    setupCamera()

    # Draw game elements
    draw_grid()
    draw_player()
    draw_enemies()

    # Draw bullets as yellow cubes
    glColor3f(1, 1, 0)  # Yellow color for bullets
    for bullet in bullets:
        glPushMatrix()
        glTranslatef(*bullet['pos'])
        # Rotate bullet to align with its movement direction
        glRotatef(90 - bullet['angle'], 0, 0, 1)  # Adjust rotation to match gun angle
        glScalef(1, 2, 1)  # Make bullets slightly elongated in movement direction
        glutSolidCube(bullet_size)
        glPopMatrix()

    # UI elements
    glColor3f(1, 1, 1)
    draw_text(20, 760, f"Lives: {player_life}  Score: {score}  Missed: {bullets_missed}/10")
    draw_text(20, 730, f"Cheat Mode: {'ON' if cheat_mode else 'OFF'}")
    draw_text(20, 700, f"Left Click: Shoot  |  Right Click: Toggle Camera  |  WASD: Move/Rotate")

    if game_over:
        draw_text(350, 400, "GAME OVER - Press R to restart")

    glutSwapBuffers()


def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)  # Removed depth testing
    glutInitWindowSize(1000, 800)
    glutCreateWindow(b"Bullet Frenzy 3D")

    # Register callbacks
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)

    init_game()
    glutMainLoop()


if __name__ == "__main__":
    main()