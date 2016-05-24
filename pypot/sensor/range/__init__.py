try:
    import smbus

    from .sonar import Sonar

except ImportError:
    print('''You need to install smbus first.
          sudo apt-get install build-essential libi2c-dev i2c-tools python-dev libffi-dev
          pip install smbus-cffi''')
