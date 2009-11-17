def do(name, *args, **kw):
    return name, args, kw

worm_letter_plans = {
    'E' : ((42, 100), [
        (((40,0),176), [
            (do('forward'), 10),
            (do('left', degrees=90.0/20), 20),
            (do('forward'), 20),
            (do('left', degrees=90.0/20), 20),
            (do('forward'), 10),
        ]),
        (((35,35),180), [
            (do('nothing'), 90),
            (do('forward'), 15),
        ]),
    ]),
    'y' : ((38, 100), [
        (((30,33),86), [
            (do('forward'), 25),
            (do('right'), 25),
        ]),
        (((0,33),90), [
            (do('nothing'), 15),
            (do('left', degrees=100.0/25), 25),
        ]),
    ]),
    'a' : ((40, 100), [
        (((0,15),-74), [
            (do('right', degrees=150.0/25), 25),
            (do('forward'), 25),
            (do('left'), 8),
        ]),
        (((30,35),180), [
            (do('nothing'), 15),
            (do('forward'), 8),
            (do('left', degrees=180.0/30), 30),
            (do('forward'), 8),
        ]),
    ]),
    'l' : ((10, 100), [
        (((0,0),85), [
            (do('forward'), 40),
        ]),
    ]),
    ' ' : ((30, 100), [
    ]),
    'L' : ((43, 100), [
        (((0,0),85), [
            (do('forward'), 30),
            (do('left'), 22),
            (do('forward'), 10),
        ]),
    ]),
    'o' : ((35, 100), [
        (((20,28),5), [
            (do('right', degrees=360.0/60), 60),
        ]),
    ]),
    't' : ((45, 100), [
        (((0,23),-5), [
            (do('forward'), 20),
        ]),
        (((15,5),85), [
            (do('forward'), 22),
            (do('left', degrees=150.0/20), 20),
        ]),
    ]),
    'e' : ((50, 100), [
        (((0,35),-5), [
            (do('forward'), 20),
            (do('left', degrees=170.0/20), 20),
            (do('forward'), 5),
            (do('left', degrees=120.0/25), 25),
            (do('left', degrees=90.0/30), 30),
        ]),
    ]),
    'm' : ((45, 100), [
        (((0,45),-95), [
            (do('forward'), 15),
            (do('right', degrees=180.0/20), 20),
            (do('forward'), 15),
        ]),
        (((40,40),-95), [
            (do('forward'), 15),
            (do('left', degrees=180.0/20), 20),
        ]),
    ]),
}
