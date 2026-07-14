from __future__ import division

import pygame as pg
from .. import setup, tools
from .. import constants as c
from .. components import collider
from .. components import bricks
from .. components import coin_box
from .. components import enemies
from .. components import checkpoint
from .. states.level1 import Level1


class Level2(Level1):
    """Second stage of the game.  Reuses the whole Level1 engine but provides
    a brand new layout of ground, pipes, steps, bricks, coin boxes and
    enemies for a fresh challenge."""

    def setup_ground(self):
        """Ground split by a couple of pits Mario must jump over"""
        ground_rect1 = collider.Collider(0,    c.GROUND_HEIGHT, 2500, 60)
        ground_rect2 = collider.Collider(2720, c.GROUND_HEIGHT, 2200, 60)
        ground_rect3 = collider.Collider(5140, c.GROUND_HEIGHT, 3860, 60)

        self.ground_group = pg.sprite.Group(ground_rect1,
                                             ground_rect2,
                                             ground_rect3)

    def setup_pipes(self):
        """Create collideable rects for all the pipes"""
        pipe1 = collider.Collider(980,  452, 83, 82)
        pipe2 = collider.Collider(1560, 409, 83, 140)
        pipe3 = collider.Collider(2150, 366, 83, 170)
        pipe4 = collider.Collider(3400, 452, 83, 82)
        pipe5 = collider.Collider(4300, 409, 83, 140)
        pipe6 = collider.Collider(6100, 452, 83, 82)
        pipe7 = collider.Collider(7000, 366, 83, 170)

        self.pipe_group = pg.sprite.Group(pipe1, pipe2, pipe3,
                                           pipe4, pipe5, pipe6,
                                           pipe7)

    def setup_steps(self):
        """A descending and an ascending staircase, plus the final
        staircase leading up to the flag pole."""
        step1 = collider.Collider(5300, 495, 40, 44)
        step2 = collider.Collider(5343, 452, 40, 44)
        step3 = collider.Collider(5386, 409, 40, 44)
        step4 = collider.Collider(5429, 366, 40, 176)

        step5 = collider.Collider(5556, 366, 40, 176)
        step6 = collider.Collider(5599, 408, 40, 40)
        step7 = collider.Collider(5642, 452, 40, 40)
        step8 = collider.Collider(5685, 495, 40, 40)

        step9  = collider.Collider(7760, 495, 40, 40)
        step10 = collider.Collider(7803, 452, 40, 40)
        step11 = collider.Collider(7845, 409, 40, 40)
        step12 = collider.Collider(7888, 366, 40, 40)
        step13 = collider.Collider(7931, 323, 40, 40)
        step14 = collider.Collider(7974, 280, 40, 40)
        step15 = collider.Collider(8017, 237, 40, 40)
        step16 = collider.Collider(8060, 194, 40, 40)
        step17 = collider.Collider(8103, 194, 40, 360)

        step18 = collider.Collider(8488, 495, 40, 40)

        self.step_group = pg.sprite.Group(step1,  step2,  step3,  step4,
                                          step5,  step6,  step7,  step8,
                                          step9,  step10, step11, step12,
                                          step13, step14, step15, step16,
                                          step17, step18)

    def setup_bricks(self):
        """Creates all the breakable bricks for the level."""
        self.coin_group = pg.sprite.Group()
        self.powerup_group = pg.sprite.Group()
        self.brick_pieces_group = pg.sprite.Group()

        brick1  = bricks.Brick(560,  365)
        brick2  = bricks.Brick(603,  365)
        brick3  = bricks.Brick(646,  365, c.SIXCOINS, self.coin_group)
        brick4  = bricks.Brick(1300, 193)
        brick5  = bricks.Brick(1343, 193)
        brick6  = bricks.Brick(1386, 193)
        brick7  = bricks.Brick(1429, 193, c.STAR, self.powerup_group)
        brick8  = bricks.Brick(2900, 365)
        brick9  = bricks.Brick(2943, 365)
        brick10 = bricks.Brick(3750, 193)
        brick11 = bricks.Brick(3793, 193)
        brick12 = bricks.Brick(3836, 193)
        brick13 = bricks.Brick(4600, 365)
        brick14 = bricks.Brick(4643, 365)
        brick15 = bricks.Brick(6300, 193)
        brick16 = bricks.Brick(6343, 193)
        brick17 = bricks.Brick(6386, 193)
        brick18 = bricks.Brick(6429, 193)
        brick19 = bricks.Brick(7200, 365)
        brick20 = bricks.Brick(7243, 365)

        self.brick_group = pg.sprite.Group(brick1,  brick2,  brick3,  brick4,
                                           brick5,  brick6,  brick7,  brick8,
                                           brick9,  brick10, brick11, brick12,
                                           brick13, brick14, brick15, brick16,
                                           brick17, brick18, brick19, brick20)

    def setup_coin_boxes(self):
        """Creates all the coin boxes and puts them in a sprite group"""
        coin_box1 = coin_box.Coin_box(603,  193, c.MUSHROOM, self.powerup_group)
        coin_box2 = coin_box.Coin_box(1386, 365, c.COIN, self.coin_group)
        coin_box3 = coin_box.Coin_box(2900, 193, c.COIN, self.coin_group)
        coin_box4 = coin_box.Coin_box(3793, 365, c.MUSHROOM, self.powerup_group)
        coin_box5 = coin_box.Coin_box(4643, 193, c.COIN, self.coin_group)
        coin_box6 = coin_box.Coin_box(6386, 365, c.COIN, self.coin_group)
        coin_box7 = coin_box.Coin_box(7243, 193, c.FIREFLOWER, self.powerup_group)

        self.coin_box_group = pg.sprite.Group(coin_box1, coin_box2, coin_box3,
                                              coin_box4, coin_box5, coin_box6,
                                              coin_box7)

    def setup_enemies(self):
        """Creates all the enemies and stores them in a list of lists."""
        goomba0 = enemies.Goomba()
        goomba1 = enemies.Goomba()
        goomba2 = enemies.Goomba()
        goomba3 = enemies.Goomba()
        goomba4 = enemies.Goomba()
        goomba5 = enemies.Goomba()
        goomba6 = enemies.Goomba()
        goomba7 = enemies.Goomba()

        koopa0 = enemies.Koopa()
        koopa1 = enemies.Koopa()

        enemy_group1 = pg.sprite.Group(goomba0)
        enemy_group2 = pg.sprite.Group(goomba1, goomba2)
        enemy_group3 = pg.sprite.Group(koopa0)
        enemy_group4 = pg.sprite.Group(goomba3, goomba4)
        enemy_group5 = pg.sprite.Group(koopa1)
        enemy_group6 = pg.sprite.Group(goomba5, goomba6, goomba7)

        self.enemy_group_list = [enemy_group1, enemy_group2, enemy_group3,
                                 enemy_group4, enemy_group5, enemy_group6]

    def setup_checkpoints(self):
        """Creates invisible checkpoints that spawn enemies and trigger the
        flag pole / castle sequence."""
        check1 = checkpoint.Checkpoint(510,  '1')
        check2 = checkpoint.Checkpoint(1300, '2')
        check3 = checkpoint.Checkpoint(2400, '3')
        check4 = checkpoint.Checkpoint(3600, '4')
        check5 = checkpoint.Checkpoint(4800, '5')
        check6 = checkpoint.Checkpoint(6200, '6')
        check7 = checkpoint.Checkpoint(8504, '11', 5, 6)
        check8 = checkpoint.Checkpoint(8775, '12')

        self.check_point_group = pg.sprite.Group(check1, check2, check3,
                                                 check4, check5, check6,
                                                 check7, check8)
