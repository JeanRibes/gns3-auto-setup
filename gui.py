# Load Gtk
import time
from math import sqrt, cos, sin

import cairo
import gi

from main import *

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk


def dist(a_x, a_y, b_x, b_y):
    return sqrt((a_x - b_x) ** 2 + (a_y - b_y) ** 2)


class Gui:
    routers: List[Router]
    cairo_scale = 1.5

    def __init__(self):
        self.app = Gtk.Application(application_id='ovh.ribes.jean.gns3.cisco-autoconf')
        self.app.connect('activate', self.on_activate)

    def run(self):
        self.app.run()

    def on_activate(self, app):
        # … create a new window…
        self.builder = Gtk.Builder()
        self.builder.add_from_file('ui.glade')
        self.win: Gtk.ApplicationWindow = self.builder.get_object('app_win')

        self.draw_area: Gtk.DrawingArea = self.builder.get_object('drawing_area')
        self.apply_btn: Gtk.Button = self.builder.get_object('apply_button')
        self.open_btn: Gtk.Button = self.builder.get_object('open_button')
        self.class_add_btn: Gtk.Button = self.builder.get_object('class_add_button')
        self.classes_vbox: Gtk.Box = self.builder.get_object('classes_box')

        self.draw_area.connect('draw', self.draw_routers)
        self.draw_area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.draw_area.connect('button-press-event', self.on_draw_area_clicked)

        self.apply_btn.connect('clicked', self.fetch_routers)
        self.class_add_btn.connect('clicked', self.add_class_hbox)

        self.win.connect('destroy', lambda x: exit(0))
        self.win.set_title("Autoconfigurateur Cisco GNS3")
        self.win.show_all()
        self.win.show()
        self.win.present_with_time(time.time())
        self.win.show()
        self.fetch_routers()

    def fetch_routers(self, *args, **kwargs):
        routers, gs, project_id, liens = get_gns_conf()
        self.routers = list(routers.values())

        min_x, min_y = 0, 0
        max_x, max_y = 0, 0
        for router in self.routers:
            if router.x < min_x:
                min_x = router.x
            if router.y < min_y:
                min_y = router.y

            if router.x > max_x:
                max_x = router.x
            if router.y > max_y:
                max_y = router.y
        min_x -= 20
        min_y -= 20
        rx = (max_x - min_x) / 2
        ry = (max_y - min_y) / 2
        for router in self.routers:
            router.x = 100 * (router.x - min_x) / rx
            router.y = 100 * (router.y - min_y) / ry

        self.draw_area.queue_draw()
        return None

    def draw_routers(self, da: Gtk.DrawingArea, cr: cairo.Context):
        cr.scale(self.cairo_scale, self.cairo_scale)
        cr.set_line_width(1)
        for router in self.routers:
            x, y = router.x + 20, router.y + 20
            print(f"{router.name} {x} {y}")
            for interface in router.interfaces:
                if interface.peer is not None:
                    ix = interface.peer.x
                    iy = interface.peer.y

                    cr.set_source_rgb(0, 1, 0)
                    cr.move_to(x, y)
                    cr.line_to(ix + 20,
                               iy + 20)
                    cr.stroke()
                    d = dist(ix, iy, router.x, router.y)
                    cx = (ix - router.x) / d
                    cy = (iy - router.y) / d

                    cr.set_source_rgb(1, 0, 0)
                    cr.rectangle((cx * 20) + x - 5,
                                 (cy * 20) + y - 5, 10, 10)
                    cr.fill()

                    cr.set_source_rgb(0, 0, 1)
                    cr.move_to((cx * 35) + x - 15,
                               (cy * 35) + y)
                    cr.show_text(f"{interface.name}")
            cr.set_source_rgb(0, 0, 0)
            cr.arc(x, y, 20, 0, 2 * 3.14)
            cr.fill()

        cr.set_font_size(12)
        for router in self.routers:
            x, y = router.x + 20, router.y + 20
            cr.move_to(x - 7, y + 3)
            cr.set_source_rgb(1, 1, 1)
            cr.show_text(f"{router.name}")

    def on_draw_area_clicked(self, widget: Gtk.DrawingArea, event: Gdk.EventButton):
        for router in self.routers:
            if abs((event.x / self.cairo_scale) - (20 + router.x)) < 20 and abs((event.y/self.cairo_scale) - (20 + router.y)) < 20:
                print(f"{router.name}")
                self.show_router_win(router)
                return True
        print(f" x={int(event.x)} y= {int(event.y)}   ")

    def add_class_hbox(self, event, classe=None):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.add(hbox)
        class_name_entry = Gtk.Entry()
        class_name_entry.set_text('nom de la classe')
        hbox.add(class_name_entry)
        save_btn = Gtk.Button(label='Enregistrer')
        hbox.add(save_btn)

        class_template_entry = Gtk.TextView()
        template_entry_b: Gtk.TextBuffer = class_template_entry.get_buffer()
        template_entry_b.set_text("#template pour cette classe ici")
        vbox.add(class_template_entry)

        values_e = Gtk.TextView()
        values_b: Gtk.TextBuffer = values_e.get_buffer()
        values_b.set_text("{'cle1':'valeur1','cle2':'valeur2'}")
        vbox.add(values_e)

        self.classes_vbox.add(vbox)

        def save_class(*args):
            ts = template_entry_b.get_start_iter()
            te = template_entry_b.get_end_iter()
            print(f"name={class_name_entry.get_text()}\ntemplate={template_entry_b.get_text(ts, te, True)}")
            print(f"values={values_b.get_text(values_b.get_start_iter(), values_b.get_end_iter(), True)}")

        save_btn.connect('clicked', save_class)
        vbox.show_all()

    def show_router_win(self,router:Router):
        win: Gtk.Window = self.builder.get_object('router_window')
        win.set_title(f"Configuration du routeur {router.name}")
        win.show_all()

if __name__ == '__main__':
    g = Gui()
    g.run()
    Gtk.main()
