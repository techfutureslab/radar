import math
import random
import serial
import multiprocessing
import Queue
import Tkinter


class RadarDisplay:
    def __init__(self, parent, size, maxDistance):
        self.size = size
        self.maxDistance = maxDistance
        self.canvas = Tkinter.Canvas(parent, width=size, height=size, bg="black")
        self.centre = (size / 2, size / 2)
        self.canvas.pack()
        self.ages = dict()
        self.msPerFrame = 33

    def blip(self, angleDegrees, distance, pointRadius=5):
        # Convert distance to pixels
        distance = float(distance) / self.maxDistance * self.size / 2

        # Calculate location of point on canvas
        angleRadians = math.radians(angleDegrees)
        deltaX = math.sin(angleRadians) * distance
        deltaY = -math.cos(angleRadians) * distance
        point = (self.centre[0] + deltaX, self.centre[1] + deltaY)

        # Draw line
        line = self.canvas.create_line(self.centre[0],
                                       self.centre[1],
                                       point[0],
                                       point[1],
                                       fill="red")
        self.ages[line] = 0

        # Draw point
        oval = self.canvas.create_oval(point[0] - pointRadius,
                                       point[1] - pointRadius,
                                       point[0] + pointRadius,
                                       point[1] + pointRadius,
                                       fill="red")
        self.ages[oval] = 0

        def animate(canvas, item, ageSpeed=0.1):
            def rgbToHex(rgb):
                return '#%02x%02x%02x' % rgb

            # Ensure that age is bounded between 0 and maxAge
            age = self.ages[item]
            if age >= 1:
                # Item is too old, delete it
                del self.ages[item]
                canvas.delete(item)
                return  # do not call animate again
            if age < 0:
                age = 0

            # Calculate how green the item should be based on age
            green = (1.0 - age) * 255

            # Set the item's colour
            canvas.itemconfigure(item, fill=rgbToHex((0, green, 0)))

            # Increase the age of the item
            self.ages[item] = age + ageSpeed

            # Call animate again
            canvas.after(self.msPerFrame, animate, canvas, item, ageSpeed)

        animate(self.canvas, line, 0.050)
        animate(self.canvas, oval, 0.0025)

    def startHandlingQueue(self, queue):
        def handleQueue(canvas, queue):
            def getData():
                try:
                    data = queue.get(False)
                    if data == "":
                        data = None
                except Queue.Empty:
                    data = None
                return data

            data = getData()
            while data is not None:
                print("Received: \"" + data + "\"")
                parts = data.split()
                if len(parts) != 2:
                    print "Did not find exactly two numbers"
                    continue

                angle = float(parts[0])
                distance = float(parts[1])

                self.blip(angle, distance)

                data = getData()

            canvas.after(self.msPerFrame, handleQueue, canvas, queue)

        handleQueue(self.canvas, queue)


queue = multiprocessing.Queue()
# queue.put("0 5")
# queue.put("45 10")
# queue.put("90 15")
command = multiprocessing.Queue()


def comms(queue, command):
    try:
        port = serial.Serial('COM7', 9600, timeout=1)
    except:
        print "Failed to open comms port; quitting comms"
        return

    while True:
        line = port.readline()
        print("Read \"" + line + "\"")
        queue.put(line)

        try:
            if command.get(False) == "quit":
                print("Quitting comms")
                return
        except Queue.Empty:
            pass


if __name__ == "__main__":
    commsProcess = multiprocessing.Process(target=comms, args=(queue, command))
    commsProcess.start()

    top = Tkinter.Tk()

    radar = RadarDisplay(top, size=1000, maxDistance=30)
    radar.startHandlingQueue(queue)
    # radar.blip(45, 20)


    # b1 = Tkinter.Button(top, text="One")
    # b2 = Tkinter.Button(top, text="Two")
    # b1.pack()
    # b2.pack()

    # def onClick():
    #    radar.blip(random.randrange(0, 180),
    #               random.randrange(0, radar.maxDistance))
    # b1.configure(command=onClick)

    top.mainloop()
    print("Quitting GUI")
    command.put("quit")
    commsProcess.join()


