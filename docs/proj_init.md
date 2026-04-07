### Proj init
    
    **Platformio**: To use platformio we have to install it via pip

    '''bash
        pip3 install -U platformio
    '''
    
    - In order to initialize the project you can use this command:

    pio project init --board [name-of-board]

### Workflow

- Open src/main.cpp and develop code implement features etc etc 
- tun 'pio run' to make the build and check for any errors
- Upload:
    * pio run -target upload
- Serial monitor:
    * pio device monitor -baud 115200

### Platformio.init check

* Check if platformio.ini as the following content:

    '''bash
    [env:esp32dev]
    platform = espressif32
    board = esp32dev
    framework = arduino
    monitor_speed = 115200
    '''
