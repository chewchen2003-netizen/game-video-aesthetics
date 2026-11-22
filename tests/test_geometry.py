import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
"""Numerical invariants for the user's formulas, independent of aesthetic grades."""
import unittest,numpy as np
from cv_measure import pos,grid,separation,overlapping,forward_from_screen
from composition_math import occlusion,look_room
class FormulaTests(unittest.TestCase):
 def test_visible_box_normalization(self):
  r=pos([20,10,80,50],100,100);self.assertEqual(r['center'],[.5,.3]);self.assertEqual(r['edge_distances'],{'left':.2,'right':.2,'top':.1,'bottom':.5})
 def test_grid_denominators_are_distinct(self):
  m=np.zeros((90,90),bool);m[:15,:30]=True;r=grid(m);self.assertAlmostEqual(r['coverage_per_cell'][0][0],.5);self.assertEqual(r['allocation_per_cell'][0][0],1);self.assertAlmostEqual(np.sum(r['allocation_per_cell']),1)
 def test_color_equal_and_separated(self):
  m=np.zeros((100,100),bool);m[30:70,30:70]=True;rgb=np.full((100,100,3),120,np.uint8);r=separation(rgb,m,np.zeros_like(m),[30,30,70,70]);self.assertAlmostEqual(r['color_JS_distance'],0);rgb[m]=[255,0,0];rgb[~m]=[0,255,0];r=separation(rgb,m,np.zeros_like(m),[30,30,70,70]);self.assertAlmostEqual(r['color_JS_distance'],1)
 def test_identical_contours_zero_distance(self):
  a=np.zeros((100,100),bool);a[20:60,20:60]=True;r=overlapping(a,a);self.assertEqual(r['geometry']['a_to_b']['min_distance_normalized'],0);self.assertEqual(r['geometry']['a_to_b']['near_contour_ratio'],1)
 def test_screen_velocity_not_world_motion(self):
  r=forward_from_screen(([10,20,30,50],0),[30,20,50,50],.25,100,100);self.assertFalse(r['actual_direction_valid']);self.assertIsNone(r['front_distance']);self.assertEqual(r['screen_speed_px_s'],80)
 def test_occlusion_requires_complete_mask(self):
  v=np.zeros((10,10),bool);f=v.copy();f[2:6,2:6]=True;v[2:4,2:6]=True;self.assertIsNone(occlusion(v,None)['ratio']);self.assertEqual(occlusion(v,f)['ratio'],.5)
 def test_look_room_uses_face_not_camera(self):
  self.assertFalse(look_room(None,None,100)['valid']);r=look_room([20,20,40,40],'right',100,'head_direction_proxy');self.assertAlmostEqual(r['front'],.6);self.assertAlmostEqual(r['back'],.2);self.assertAlmostEqual(r['ratio'],.75)
if __name__=='__main__':unittest.main()
