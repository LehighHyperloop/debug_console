import atexit
import cmd
import code
import os
import paho.mqtt.client as mqtt
import readline
import sys

cmd_tree = {
    "subscribe": None,
    "unsubscribe": None,
    "ack": None,
    "set": {
        "levitation": [ "STOPPED", "RUNNING" ],
        "braking": [ "ON", "OFF" ]
    }
}

custom_subs = []

class ConsoleCmd(cmd.Cmd):
    def do_subscribe(self, line):
        client.subscribe(line)
        custom_subs.append(line)

    def do_unsubscribe(self, line):
        if line == "":
            client.unsubscribe(custom_subs)
        else:
            client.unsubscribe(line)

    def do_ack(self, line):
        client.publish("cmd", "ack")

    def do_set(self, line):
        client.publish("cmd", "set " + line)

    def completedefault(self, text, line, start_index, end_index):
        s = line.split(" ")
        top = cmd_tree

        if len(s) > 1:
            try:
                for k in s[0:-1]:
                    top = top[k]
            except KeyError:
                return None

        if isinstance(top, list):
            return [
                v for v in top
                if v.startswith(text)
            ]
        else:
            return [
                k for k,v in top.iteritems()
                if k.startswith(text)
            ]

def complete(text, state):
    line = readline.get_line_buffer()
    try:
        return [ x + " " for x in cmds if x.startswith(text)][state]
    except IndexError:
        return None

class HistoryConsole(code.InteractiveConsole):
    def __init__(self, locals=None, filename="<console>",
                 histfile=os.path.expanduser("~/.console-history")):
        code.InteractiveConsole.__init__(self, locals, filename)
        self.init_history(histfile)

    def init_history(self, histfile):
        readline.set_completer(complete)
        readline.parse_and_bind("tab: complete")
        if hasattr(readline, "read_history_file"):
            try:
                readline.read_history_file(histfile)
            except IOError:
                pass
            atexit.register(self.save_history, histfile)

    def save_history(self, histfile):
        readline.set_history_length(1000)
        readline.write_history_file(histfile)

# Setup client
client = mqtt.Client()
mqtt_IP = os.environ["MQTT_IP"]
client.connect(mqtt_IP, 1883)
client.loop_start()

def print_console(t):
    sys.stdout.write('\r'+' '*(len(readline.get_line_buffer())+2)+'\r')
    print(t)
    sys.stdout.write('> ' + readline.get_line_buffer())
    sys.stdout.flush()

def on_message(mosq, obj, msg):
    print_console(msg.topic + ": " + msg.payload)

client.subscribe("debug/#")
client.on_message = on_message

console = HistoryConsole()

# Loop in main
console = ConsoleCmd()
console.prompt = '> '
console.cmdloop()
#while True:
#    try:
#        line = raw_input('> ')
#        if line:
#            client.publish("cmd", line)
#    except KeyboardInterrupt:
#        print ""
#        pass
#    except EOFError:
#        # End of file
#        break

client.loop_stop()
