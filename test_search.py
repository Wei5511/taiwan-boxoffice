import sys
sys.path.append('.')
from main import list_movies
import traceback

try:
    print(list_movies(search='test'))
except Exception as e:
    traceback.print_exc()
