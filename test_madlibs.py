"""Tests for madlibs-gan."""
import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from madlibs import (
    MadlibsGAN, MadlibsCell, PARADIGMS, fnv1a_64,
)


class TestFNV1a(unittest.TestCase):
    def test_fleet_canary(self):
        self.assertEqual(fnv1a_64('café Δ 日本語'), '0x24a555471370b18d')


class TestParadigms(unittest.TestCase):
    def test_all_paradigms_have_slots(self):
        for name, p in PARADIGMS.items():
            self.assertIn('slots', p, f'{name} missing slots')
            self.assertIn('description', p, f'{name} missing description')
            self.assertIn('example', p, f'{name} missing example')
    
    def test_image_description_paradigm(self):
        p = PARADIGMS['image_description']
        self.assertIn('target', p['slots'])
        self.assertIn('palette', p['slots'])


class TestMadlibsCell(unittest.TestCase):
    def test_creation(self):
        cell = MadlibsCell(cell_id='m1', paradigm='image_description', producer='qwen')
        self.assertEqual(cell.paradigm, 'image_description')
        self.assertEqual(cell.jev_score, 0.0)


class TestMadlibsGAN(unittest.TestCase):
    def test_creation(self):
        g = MadlibsGAN(paradigm_name='image_description', topic='a sunset')
        self.assertEqual(g.paradigm_name, 'image_description')
        self.assertEqual(g.producer, 'qwen')
        self.assertEqual(g.filler, 'deepseek')
    
    def test_producer_template(self):
        g = MadlibsGAN(paradigm_name='image_description', topic='a sunset')
        paradigm = PARADIGMS['image_description']
        template = g._producer_template(paradigm, 1)
        # Should at least have entries for each slot
        self.assertGreaterEqual(len(template), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
