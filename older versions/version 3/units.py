# units.py
import numpy as np
import random
from config import TARGET_POSITION1, TARGET_POSITION2, SEPARATION_DISTANCE
from config import Singleton, UnitManager, BulletManager, Wall, WALLS
from bullets import Bullet

team1_units = []
team2_units = []
team1_bullets = []
team2_bullets = []

class Unit:
    def __init__(self, damage, health, speed, team):
        self.damage = damage
        self.health = health
        self.speed = speed
        self.max_speed = speed / 4 # Maximum speed for this unit
        self.attack_speed = speed
        self.cooldown = (int(60/speed) if speed > 0 else 100)
        self.attack_range = 20
        self.vision_range = 200
        self.position = np.array([0.0, 0.0], dtype=float)  # Starting position
        self.velocity = np.array([0.0, 0.0], dtype=float)  # Starting velocity
        self.color = self.compute_color()  # Calculate color based on stats
        self.cost = damage + health + speed
        self.radius = 10
        self.team = team

    def compute_color(self):
        """Compute RGB color based on damage, speed, and health."""
        r = min(int((self.damage / 10) * 255), 255)  # Normalize to 0-255
        g = min(int((self.speed / 10) * 255), 255)  # Normalize to 0-255
        b = min(int((self.health / 10) * 255), 255)  # Normalize to 0-255
        return (r, g, b)  # Return RGB tuple representing the color

    def __str__(self):
        return f"Unit(Damage={self.damage}, Health={self.health}, Speed={self.speed}, Color={self.color})"

    def move_towards(self, target):
        """Move towards a given target position."""
        direction = target - self.position  # Direction vector
        if np.linalg.norm(direction) > 0:  # Avoid division by zero
            direction /= np.linalg.norm(direction)  # Normalize
            direction *= self.max_speed
        return direction.astype(float)  # Return normalized and scaled velocity

    def pursue_enemy(self, enemy_position):
        """Pursue a given enemy's position."""
        return self.move_towards(enemy_position)

    def separation_and_collision_avoidance(self, units, separation_distance):
        """Avoid collisions with other units using a separation distance."""
        steering = np.zeros_like(self.position)  # Initialize a zero vector
        for other_unit in units + WALLS: # handle collisions with both units and walls
            if other_unit != self or isinstance(other_unit, Wall):
                distance = np.linalg.norm(self.position - other_unit.position)
                if distance < separation_distance:
                    diff = (self.position - other_unit.position)
                    diff /= distance  # Normalize and weight by distance
                    steering += diff  # Add to steering for collision avoidance
        return steering

    def update(self, target, enemy_position, units, separation_distance, dt):
        """Update unit velocity and position based on behaviors."""
        # Weights for cohesion, pursuit, and separation
        cohesion_weight = 0.05
        pursuit_weight = 0.7
        separation_weight = 0.25
        
        # Compute desired velocities for different behaviors
        cohesion = self.move_towards(target) * cohesion_weight
        pursuit = self.pursue_enemy(enemy_position) * pursuit_weight
        separation = self.separation_and_collision_avoidance(units, separation_distance)/np.sqrt(len(units)) * separation_weight
        
        # Combine behaviors to determine desired velocity
        desired_velocity = cohesion + pursuit + separation
        self.velocity = np.clip(desired_velocity, -self.max_speed, self.max_speed)  # Limit to max speed
        self.position += self.velocity * dt  # Update position, take care about delta time

        # Decrease cooldown
        self.cooldown = max(0, self.cooldown - 1)

    # A method to handle attacks
    def attack(self, target_unit, dt):
        """Attack a target unit."""
        if self.cooldown == 0:
            target_unit.health -= self.damage  # Reduce the target's health based on attacker's attack power
            if target_unit.health <= 0:

                # Remove the target unit if its health drops to zero or below
                unit_manager = UnitManager()
                if target_unit.team == "team1":
                    unit_manager.team1_units.remove(target_unit)
                elif target_unit.team == "team2":
                    unit_manager.team2_units.remove(target_unit)
            
            if self.attack_speed > 0:
                self.cooldown = int(1/self.attack_speed/dt)
        else:
        # Decrease cooldown based on delta time
            self.cooldown = max(0, self.cooldown - 1)



class Ranged_Unit(Unit):
    def __init__(self, damage, health, speed, team):
        super().__init__(damage, health, speed, team)
        self.is_attacking = False
        self.attack_range = self.attack_range + 200

    def attack(self, target_unit, dt):
        if self.cooldown == 0:
            self.is_attacking = True
            bullet_velocity = target_unit.position - self.position
            bullet_velocity /= np.linalg.norm(bullet_velocity)
            bullet_velocity *= self.attack_speed
            
            # Create bullet with correct team
            bullet = Bullet(position=self.position,
                            velocity=bullet_velocity,
                            damage=self.damage,
                            color=self.color,
                            team=self.team) # Team affiliation of the bullet
            
            # Add bullet to the correct list based on the unit's team
            bullet_manager = BulletManager()

            if self.team == "team1":
                bullet_manager.team1_bullets.append(bullet)
            else:
                bullet_manager.team2_bullets.append(bullet)
            
            if self.attack_speed > 0:
                self.cooldown = int(60 / self.attack_speed / dt)

            # Send attack to cooldown
            if self.attack_speed > 0:
                self.cooldown = int(60 / self.attack_speed)
        else:
            self.cooldown = max(0, self.cooldown - 1)

