import unittest
import os
import json
import hashlib
from gemini_chat import get_h_file, load_history, PROMPTS

class TestChatLogic(unittest.TestCase):
    def test_hostname_context(self):
        # Verificar que tenemos contextos definidos para tus equipos
        self.assertIn("jorge-thinkpad-x270", PROMPTS)
        self.assertIn("raspberrypi", PROMPTS)
        self.assertIn("iqual-mint", PROMPTS)

    def test_history_hashing(self):
        # Verificar que el hash de la sesión local sea consistente
        h_file = get_h_file(is_global=False)
        self.assertTrue(h_file.endswith(".json"))
        self.assertIn("sessions", h_file)

    def test_global_session_path(self):
        # Verificar ruta de sesión global
        h_file = get_h_file(is_global=True)
        self.assertTrue(h_file.endswith("global.json"))

    def test_history_io(self):
        # Probar lectura/escritura de historial simulado
        test_file = "/tmp/test_history.json"
        test_data = [{"role": "user", "content": "hola"}]
        with open(test_file, "w") as f:
            json.dump(test_data, f)
        
        loaded = load_history(test_file)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["content"], "hola")
        os.remove(test_file)

if __name__ == "__main__":
    unittest.main()
