#!../.venv/bin/python3

from __future__ import annotations
from enum import Enum

import pyglet
import os
import time
import glob
import subprocess

RESOURCES_PATH = "./resources"

# TODO: draw shapes with OpenGL POINTS UIBezeithPath

class UIObject:
	pass


class UIColor:

	def __init__(self, hex):
		rgb_color = hex.lstrip('#')
		if len(hex) == 6:
			self.r, self.g, self.b = tuple(int(rgb_color[i:i+2], 16) for i in (0, 2, 4))
			self.a = 255
		elif len(hex) == 8:
			self.r, self.g, self.b, self.a = tuple(int(rgb_color[i:i+2], 16) for i in (0, 2, 4, 6))

		self.rgb = (self.r, self.g, self.b)
		self.rgba = (self.r, self.g, self.b, self.a)

	def get_rgba(self, opacity):
		return self.rgba if opacity == 100 else (self.r, self.g, self.b, round(opacity / 100 * 255))


# TODO: gradient from scratch (draw lines)
class CGGradientPoint:

	def __init__(self, color: UIColor, position: float, mid_point: float, opacity: int):
		self.color = color
		self.position = position
		self.mid_point = mid_point
		self.opacity = opacity


class CGGradientLayer:

	def __init__(self):
		self.points: list[CGGradientPoint] = []


class UIScreen:

	def __init__(self, x=0, y=0, width=0, height=0):
		# try calculate location for creating window
		self.x = x
		self.y = y
		self.width = width
		self.height = height


class UIWindow:

	def __init__(self, x=0, y=0, width=0, height=0, title="UIKit", view_controller: type[UIViewController] = None, screen=UIScreen()):
		self.x = x
		self.y = y
		self.width = width
		self.height = height
		self.screen = screen
		self.title = title
		self.view_controller = view_controller()
		self.view_controller.view.width = width
		self.view_controller.view.height = height
		self.view_controller.window = self
		self.exit = False


	def create(self):
		if self.width == 0:
			self.width = self.screen.width
			self.view_controller.view.width = self.width
		if self.height == 0:
			self.height = self.screen.height
			self.view_controller.view.height = self.height
		self.canvas = pyglet.window.Window(
			width = self.width,
			height = self.height,
			caption = self.title
		)
		self.canvas.set_location(self.x, self.y)
		cursor = self.canvas.get_system_mouse_cursor(self.canvas.CURSOR_HAND)
		self.canvas.set_mouse_cursor(cursor)

		self.batch = pyglet.graphics.Batch()

		# events
		self.canvas.on_mouse_press = self._on_mouse_press
		self.canvas.on_draw = self.draw

		self.view_did_load()

	def view_did_load(self):
		self.view_controller.view_did_load()
		for child_view_controller in self.view_controller.children:
			child_view_controller.view_did_load()


	def draw(self):
		self.canvas.clear()
		self.batch.draw()

		self.view_controller.view.draw(self.batch)
		for view in self.view_controller.view.subviews:
			view.draw(self.batch)

		for child_view_controller in self.view_controller.children:
			child_view_controller.view.draw(self.batch)
			for view in child_view_controller.view.subviews:
				view.draw(self.batch)

	def _on_mouse_press(self, x, y, button, modifiers):
		# TODO: check for children view controller's views
		for view in self.view_controller.view.subviews:
			if view.x <= x <= view.x + view.width and view.y <= y <= view.y + view.height:
				view.mouse_down(view.arg)
				return

	def close(self):
		self.exit = True


class UIApplication:

	def __init__(self, windows: list[UIWindow]):
		self.state = 0
		self.windows = windows

		# 0 - main display in system
		self.screens = []
		for pyscreen in pyglet.canvas.Display().get_screens():
			self.screens.append(UIScreen(x=pyscreen.x, y=pyscreen.y, width=pyscreen.width, height=pyscreen.height))

	def run(self):
		for window in self.windows:
			# TODO: let user change screen to draw window
			window.screen = self.screens[0]
			window.create()
		pyglet.app.run()


class UIViewController:

	def __init__(self):
		self.view = UIView(0, 0, 0, 0)
		self.window: UIWindow = None
		self.parent: UIViewController = None
		self.children: list[UIViewController] = []

	def view_did_load(self):
		pass

	def present(self, view_controller: UIViewController):
		print("present")
		view_controller.window = self.window
		view_controller.parent = self
		view_controller.view.width = self.window.width
		view_controller.view.height = self.window.height
		self.window.view_controller = view_controller
		self.children.append(view_controller)
		self.window.view_did_load()


class UIEvent(Enum):
	press = "press"


class UIResponder:

	# TODO: pass args instead of arg
	arg = None

	def mouse_down(self, arg):
		pass


class UIView(UIResponder):

	def __init__(self, x=0, y=0, width=0, height=0, background_color: UIColor = UIColor("000000"), stroke_color: UIColor = UIColor("000000"), stroke_width=0, opacity=100):
		self.x = x
		self.y = y
		self.width = width
		self.height = height
		self.background_color = background_color
		self.stroke_color = stroke_color
		self.stroke_width = stroke_width
		self.opacity = opacity

		self.subviews: list[UIView] = []

	def add_subview(self, view: UIView):
		# TODO: think about this decision
		view.x += self.x
		view.y += self.y
		self.subviews.append(view)

	def draw(self, batch):
		# TODO: add rounded rectangle (maybe replace with OpenGL GL_POINTS)
		pyglet.shapes.Rectangle(self.x, self.y, self.width, self.height, color=self.background_color.get_rgba(opacity=self.opacity), batch=batch).draw()
		if self.stroke_width != 0:
			pyglet.shapes.Rectangle(self.x - self.stroke_width, self.y, self.stroke_width, self.height + self.stroke_width, color=self.stroke_color.get_rgba(opacity=self.opacity), batch=batch).draw()
			pyglet.shapes.Rectangle(self.x, self.y + self.height, self.width + self.stroke_width, self.stroke_width, color=self.stroke_color.get_rgba(opacity=self.opacity), batch=batch).draw()
			pyglet.shapes.Rectangle(self.x + self.width, self.y - self.stroke_width, self.stroke_width, self.height + self.stroke_width, color=self.stroke_color.get_rgba(opacity=self.opacity), batch=batch).draw()
			pyglet.shapes.Rectangle(self.x - self.stroke_width, self.y - self.stroke_width, self.width + self.stroke_width, self.stroke_width, color=self.stroke_color.get_rgba(opacity=self.opacity), batch=batch).draw()
		for view in self.subviews:
			view.draw(batch)
			# pyglet.shapes.Rectangle(self.x + view.x, self.y + view.y, view.width, view.height, color=view.background_color.get_rgba(opacity=view.opacity), batch=batch).draw()
			# TODO: perform formulas for strokes
			# if view.stroke_width != 0:
			# 	pyglet.shapes.Rectangle(view.x - view.stroke_width, view.y, view.stroke_width, view.height + view.stroke_width, color=self.stroke_color.get_rgba(opacity=self.opacity), batch=batch).draw()
			# 	pyglet.shapes.Rectangle(view.x, view.y + view.height, view.width + self.stroke_width, self.stroke_width, color=self.stroke_color.get_rgba(opacity=self.opacity), batch=batch).draw()
			# 	pyglet.shapes.Rectangle(view.x + view.width, view.y - view.stroke_width, view.stroke_width, self.height + self.stroke_width, color=self.stroke_color.get_rgba(opacity=self.opacity), batch=batch).draw()
			# 	pyglet.shapes.Rectangle(view.x - view.stroke_width, view.y - view.stroke_width, view.width + self.stroke_width, self.stroke_width, color=self.stroke_color.get_rgba(opacity=self.opacity), batch=batch).draw()


class UIImage(UIView):

	# TODO: background color is not supported
	def __init__(self, x, y, width, height, path="", background_color = UIColor("000000")):
		super().__init__(x, y, width, height, background_color=background_color)
		# !!! Force running from directory upper than build. <./build/app>
		# self.path = f"{os.getcwd()}/{path}"
		self.path = path

	def draw(self, batch):
		try:
			image = pyglet.image.load(self.path)
			image.x = self.x
			image.y = self.y
			image.width = self.width
			image.height = self.height
			image.blit(image.x, image.y)
		except FileNotFoundError:
			super().draw(batch)


class UIControl(UIView):
	pass


class UIFont(UIObject):

	def __init__(self, name):
		self.name = name
		pyglet.font.add_directory(f"{RESOURCES_PATH}/fonts/Aristotelica Small Caps")
		pyglet.font.add_directory(f"{RESOURCES_PATH}/fonts/Gabriely")
		if not pyglet.font.have_font("Aristotelica Small Caps"):
			print("FONT NOT LOADED!")
			exit(1)


class UIHorizonalTextAlignment(Enum):
	left = "left"
	center = "center"
	right = "right"


class UIVerticalTextAlignment(Enum):
	top="top"
	center="center"
	bottom="bottom"


class UITextStyle(Enum):
	regular="regular"
	italic="italic"
	bold="bold"
	stretch="stretch"


class UIText(UIView):

	def __init__(self, x, y, width, height, font: UIFont, font_size: int, text="", h_align: UIHorizonalTextAlignment=UIHorizonalTextAlignment.left, v_align: UIVerticalTextAlignment=UIVerticalTextAlignment.center, style: UITextStyle = UITextStyle.regular,  text_color: UIColor = UIColor("000000"), background_color: UIColor = UIColor("000000"), stroke_color: UIColor = UIColor("000000"), stroke_width=0, opacity=100, text_padding=0):
		self.text = text
		self.style = style
		self.font = font
		self.font_size = font_size
		self.text_color = text_color
		self.background_color = background_color
		self.h_align = h_align
		self.v_align = v_align
		self.text_padding = text_padding # horizonal
		# TODO: move to UIView
		self.drawing = None
		super().__init__(x, y, width, height, background_color, stroke_color, stroke_width, opacity)

	def draw(self, batch):
		# info(f"DRAW UIText {self.x, self.y, self.width, self.height}, {self.background_color.rgba}")
		if self.drawing is not None: self.drawing()
		super().draw(batch)

		text_x = self.x
		if self.h_align == UIHorizonalTextAlignment.left:
			text_x = self.x + self.text_padding
		if self.h_align == UIHorizonalTextAlignment.center:
			text_x = self.x + self.width // 2
		if self.h_align == UIHorizonalTextAlignment.right:
			text_x = self.x + self.width - self.text_padding

		text_y = self.y
		if self.v_align == UIVerticalTextAlignment.top:
			text_y = self.y + self.height
		if self.v_align == UIVerticalTextAlignment.center:
			text_y = self.y + self.height // 2.1

		pyglet.text.Label(self.text, font_name=self.font.name, bold=True if self.style is UITextStyle.bold else False, italic=True if self.style is UITextStyle.italic else False, font_size=self.font_size, x=text_x, y=text_y,
						  anchor_y=self.v_align.value, anchor_x=self.h_align.value, color=self.text_color.get_rgba(opacity=self.opacity)).draw()

# TODO: back uibutton with text
class UIButton(UIView):

	def add_target(self, action, event: UIEvent, arg):
		if event is UIEvent.press:
			self.mouse_down = action
			self.arg = arg


class UITextInput(UIText):

	def __init__(self, text, x, y, width, height, font: UIFont, h_align: UIHorizonalTextAlignment, v_align: UIVerticalTextAlignment, style: UITextStyle = UITextStyle.regular, text_color: UIColor = UIColor("000000"), background_color: UIColor = UIColor("000000"), opacity=100, text_padding=0):
		super().__init__(text, x, y, width, height, font, h_align, v_align, style, text_color, background_color, opacity, text_padding)


gabriely_font = UIFont(
	"Gabriely Extra Light"
)
arisotelica_font = UIFont(
	"Aristotelica Small Caps"
)

light_gray_color = UIColor("E7E7E7")
gray_color = UIColor("525252")


class BaseViewController(UIViewController):

	def update_time(self):
		from datetime import datetime
		now = datetime.now()
		formatted_datetime = now.strftime("%d.%m.%Y %H:%M")
		self.date_time_text.text = formatted_datetime

	def __init__(self):
		super().__init__()
		self.status_text = UIText(
			x = 168,
			# y = 872,
			y = 1080 - 109 - 84,
			width=1684,
			height=109,
			background_color=light_gray_color,
			text="АНДРЕЙ АРУТЮНЯН",
			font=arisotelica_font,
			font_size = 80,
			text_color=UIColor("535353"),
			v_align=UIVerticalTextAlignment.center
		)

		self.line1 = UIView(
			x = 168,
			y = 1080 - 3 - 183,
			width=1704,
			height=3,
			background_color=UIColor("525252")
		)

		self.line2 = UIView(
			x = 168,
			y = 1080 - 3 - 188,
			width=1704,
			height=3,
			background_color=UIColor("525252")
		)

		self.tab_bar_view = UIView(
			x = 0,
			y = 1030,
			width = 1920,
			height = 50,
			background_color=UIColor("ABABAB")
		)

		self.date_time_text = UIText(
			text="06.08.2024 17:16",
			x = 1486,
			y = 1030,
			width=387,
			height=50,
			font=gabriely_font,
			font_size=48,
			style=UITextStyle.bold,
			text_color=UIColor("FFFFFF"),
			h_align=UIHorizonalTextAlignment.right,
			background_color=UIColor("ABABAB")
		)

		self.logo_image = UIImage(
			x = 50,
			y = 882,
			width = 109,
			height = 109,
			path=f"{RESOURCES_PATH}/images/logo.png"
		)

	def view_did_load(self):
		self.date_time_text.drawing = self.update_time
		self.view.add_subview(self.tab_bar_view)
		self.view.add_subview(self.date_time_text)
		self.view.add_subview(self.logo_image)
		self.view.add_subview(self.status_text)
		self.view.add_subview(self.line1)
		self.view.add_subview(self.line2)
		self.view.background_color = light_gray_color


class AppViewContoller(BaseViewController):

	def __init__(self):
		super().__init__()
		self.ids = None
		self.back_button = UIButton(
			x=45,
			y=1080-196-72,
			width=606,
			height=72,
			stroke_color=gray_color,
			stroke_width=1,
			background_color=light_gray_color
		)
		self.back_button_icon = UIImage(
			x=53,
			y=1080-197-68,
			width=37,
			height=68,
			path=f"{RESOURCES_PATH}/images/backbutton_icon.png",
			background_color=light_gray_color
		)
		self.back_button_text = UIText(
			x=108,
			y=1080-204-60,
			width=498,
			height=60,
			h_align=UIHorizonalTextAlignment.left,
			font_size=50,
			font=arisotelica_font,
			background_color=light_gray_color,
			text="НАЗАД",
			text_color=gray_color
		)
		# TODO: make with parent
		self.back_button.add_target(action=self.present, event=UIEvent.press, arg=MainViewController())

	def view_did_load(self):
		super().view_did_load()
		self.view.add_subview(self.back_button)
		self.view.add_subview(self.back_button_icon)
		self.view.add_subview(self.back_button_text)

	def present(self, view_controller: UIViewController):
		self.kill_app()
		super().present(view_controller)

	def run_app(self, command, app):
		subprocess.Popen(command)
		time.sleep(2)
		os.environ['DISPLAY'] = ':0'
		result = subprocess.run(['xdotool', 'search', '--name', app], stdout=subprocess.PIPE, text=True)
		output = result.stdout.strip()
		window_ids = output.splitlines()
		self.ids = window_ids.pop(0)

		for id in self.ids:
			os.system(f"xdotool windowmove {id} 45 284")
			os.system(f"xdotool windowsize {id} 1830 711")

			with open(f"{RESOURCES_PATH}/log", "w") as f:
				f.write(f"{app} + {id}\n")
				f.write(f"xdotool windowmove {id} 45 284\n")
				f.write(f"xdotool windowsize {id} 1830 711\n")
				f.write(f"xdotool windowkill {id}\n")

	def kill_app(self):
		if self.ids is not None:
			for id in self.ids:
				os.system(f"xdotool windowkill {id}")


class MainAppView(UIButton):

	def __init__(self, x=0, y=0, width=0, height=0, background_color: UIColor = UIColor("000000"), stroke_color: UIColor = UIColor("000000"), stroke_width=0, opacity=100):
		super().__init__(x, y, width, height, background_color, gray_color, 1, opacity)
		self.icon_image = UIImage(
			x = 30,
			y = 760  - 45 - 110,
			width = 150,
			height = 110
		)

		self.notif_text = UIText(
			x = 30,
			y = 760 - 250 - 325,
			width=200,
			height=325,
			font_size=350,
			text_color=UIColor("E3D800"),
			font=gabriely_font,
			background_color=light_gray_color
		)

		self.appname_text = UIText(
			x = 35,
			y = 760 - 660 - 80,
			width=540,
			height=82,
			font=arisotelica_font,
			font_size=72,
			text_color=gray_color,
			background_color=light_gray_color
		)
		self.add_subview(self.icon_image)
		self.add_subview(self.notif_text)
		self.add_subview(self.appname_text)


class MailAppView(MainAppView):

	def __init__(self, x=0, y=0, width=0, height=0, background_color: UIColor = UIColor("000000"), stroke_color: UIColor = UIColor("000000"), stroke_width=0, opacity=100):
		super().__init__(x, y, width, height, background_color, stroke_color, stroke_width, opacity)
		self.icon_image.path = f"{RESOURCES_PATH}/images/mail_icon.png"
		self.notif_text.text = "1"
		self.appname_text.text = "ЭЛ. ПОЧТА"


class FilesAppView(MainAppView):

	def __init__(self, x=0, y=0, width=0, height=0, background_color: UIColor = UIColor("000000"), stroke_color: UIColor = UIColor("000000"), stroke_width=0, opacity=100):
		super().__init__(x, y, width, height, background_color, stroke_color, stroke_width, opacity)
		self.icon_image.path = f"{RESOURCES_PATH}/images/files_icon.png"
		self.notif_text.text = "0"
		self.appname_text.text = "ФАЙЛЫ"
		self.icon_image.width = self.icon_image.height = 150
		self.icon_image.y = 760 - 150 - 34 + 70
		self.appname_text.text_color = UIColor("525252")
		self.notif_text.text_color = UIColor("ABABAB")


class FuncAppView(MainAppView):

	def __init__(self, x=0, y=0, width=0, height=0, background_color: UIColor = UIColor("000000"), stroke_color: UIColor = UIColor("000000"), stroke_width=0, opacity=100):
		super().__init__(x, y, width, height, background_color, stroke_color, stroke_width, opacity)
		self.icon_image.path = f"{RESOURCES_PATH}/images/func_icon.png"
		self.icon_image.width = 150
		self.icon_image.height = 140
		self.icon_image.y = 760 - 140 - 34 + 70
		self.notif_text.text = "1"
		self.appname_text.text = "ФУНКЦИИ"


class MainViewController(BaseViewController):

	def __init__(self):
		super().__init__()
		self.mail_app_view = MailAppView(
			x = 45,
			y = 1080 - 256 - 760,
			width = 606,
			height = 760,
			background_color=light_gray_color
		)

		self.files_app_view = FilesAppView(
			x = 657,
			y = 1080 - 256 - 760,
			width = 606,
			height = 760,
			background_color=light_gray_color
		)

		self.func_app_view = FuncAppView(
			x = 1269,
			y = 1080 - 256 - 760,
			width = 606,
			height = 760,
			background_color=light_gray_color
		)

	def view_did_load(self):
		super().view_did_load()
		self.mail_app_view.add_target(action=self.present, event=UIEvent.press, arg=MailViewContoller())
		self.files_app_view.add_target(action=self.present, event=UIEvent.press, arg=FilesViewController())
		self.func_app_view.add_target(action=self.present, event=UIEvent.press, arg=FuncViewController())
		self.view.add_subview(self.mail_app_view)
		self.view.add_subview(self.files_app_view)
		self.view.add_subview(self.func_app_view)


class MailViewContoller(AppViewContoller):

	def __init__(self):
		super().__init__()

	def view_did_load(self):
		self.status_text.text += " // ЭЛ. ПОЧТА"
		self.run_app(['thunderbird'], "Thunderbird")
		super().view_did_load()


class FilesViewController(AppViewContoller):

	def view_did_load(self):
		self.status_text.text += " // ФАЙЛЫ"
		self.run_app(['nautilus', "/home/parallels/"], "Home")
		super().view_did_load()


class FuncViewController(AppViewContoller):

	# TODO: add scroll views
	func_button = UIButton(
		x=45,
		y=1080 - 284 - 115,
		width=606,
		height=115,
		background_color=UIColor("E3D800"),
		stroke_width=1,
		stroke_color=UIColor("525252")
	)

	func_button_text = UIText(
		x=69,
		y=1080-305-72,
		width=546,
		height=72,
		font=arisotelica_font,
		font_size=32,
		h_align=UIHorizonalTextAlignment.left,
		v_align=UIVerticalTextAlignment.center,
		text="УПРАВЛЕНИЕ ПРОЕКТОРОМ",
		text_color=gray_color,
		background_color=UIColor("E3D800")
	)

	tmp_block1 = UIImage(
		x=45,
		y=1080-404-115,
		width=606,
		height=115,
		path=f"{RESOURCES_PATH}/images/tmp_block.png"
	)

	tmp_block2 = UIImage(
		x=45,
		y=1080-524-115,
		width=606,
		height=115,
		path=f"{RESOURCES_PATH}/images/tmp_block.png"
	)

	tmp_block3 = UIImage(
		x=45,
		y=1080-644-115,
		width=606,
		height=115,
		path=f"{RESOURCES_PATH}/images/tmp_block.png"
	)

	tmp_block4 = UIImage(
		x=45,
		y=1080-764-115,
		width=606,
		height=115,
		path=f"{RESOURCES_PATH}/images/tmp_block.png"
	)

	tmp_block5 = UIImage(
		x=45,
		y=1080-884-115,
		width=606,
		height=115,
		path=f"{RESOURCES_PATH}/images/tmp_block.png"
	)

	scroll_bar = UIView(
		x=659,
		y=1080-284-712,
		width=9,
		height=712,
		background_color=UIColor("ffffff")
	)

	line_1 = UIView(
		x=678,
		y=1080-284-1,
		width=1195,
		height=1,
		background_color=gray_color
	)

	line_2 = UIView(
		x=678,
		y=1080-399-1,
		width=1195,
		height=1,
		background_color=gray_color
	)

	line_3 = UIView(
		x=678,
		y=1080-759-1,
		width=1195,
		height=1,
		background_color=gray_color
	)

	func_text = UIText(
		x=687,
		y=1080-306-72,
		width=665,
		height=72,
		font=arisotelica_font,
		font_size=48,
		h_align=UIHorizonalTextAlignment.left,
		v_align=UIVerticalTextAlignment.center,
		text="УПРАВЛЕНИЕ ПРОЕКТОРОМ",
		text_color=gray_color,
		background_color=light_gray_color
	)

	func_descr_text = UIText(
		x=680,
		y=1080-431-144,
		width=1194,
		height=144,
		font=arisotelica_font,
		font_size=24,
		h_align=UIHorizonalTextAlignment.left,
		v_align=UIVerticalTextAlignment.top,
		text_color=gray_color,
		text="""
В случае если проектор не включился, убедитесь, что его индикатор горит зеленым цветом. Если это не так попробуйте включить его, используя пульт.
После выключения проектора убедитесь, что его индикатор перестал гореть каким-либо цветом.
		""",
		background_color=light_gray_color
	)

	on_button = UIButton(
		x=840,
		y=1080-767-115,
		width=906,
		height=115,
		stroke_width=1,
		stroke_color=gray_color,
		background_color=light_gray_color
	)

	on_button_text = UIText(
		x=840,
		y=1080-767-115,
		width=906,
		height=115,
		font=arisotelica_font,
		font_size=30,
		h_align=UIHorizonalTextAlignment.center,
		v_align=UIVerticalTextAlignment.center,
		text_color=gray_color,
		background_color=light_gray_color,
		text="Включить проектор"
	)

	off_button = UIButton(
		x=840,
		y=1080-890-115,
		width=906,
		height=115,
		stroke_width=1,
		stroke_color=gray_color,
		background_color=light_gray_color,
		opacity=20
	)

	off_button_text = UIText(
		x=840,
		y=1080-890-115,
		width=906,
		height=115,
		font=arisotelica_font,
		font_size=30,
		h_align=UIHorizonalTextAlignment.center,
		v_align=UIVerticalTextAlignment.center,
		text_color=gray_color,
		background_color=light_gray_color,
		opacity=20,
		text="Выключить проектор"
	)

	def turn_on(self, arg):
		self.on_button_text.opacity = 20
		self.on_button.opacity = 20
		self.off_button_text.opacity = 100
		self.off_button.opacity = 100

	def turn_off(self, arg):
		self.off_button_text.opacity = 20
		self.off_button.opacity = 20
		self.on_button_text.opacity = 100
		self.on_button.opacity = 100


	def view_did_load(self):
		self.status_text.text += " // ФУНКЦИИ"
		self.view.add_subview(self.func_button)
		self.view.add_subview(self.func_button_text)

		self.view.add_subview(self.tmp_block1)
		self.view.add_subview(self.tmp_block2)
		self.view.add_subview(self.tmp_block3)
		self.view.add_subview(self.tmp_block4)
		self.view.add_subview(self.tmp_block5)

		self.view.add_subview(self.scroll_bar)
		self.view.add_subview(self.line_1)
		self.view.add_subview(self.line_2)
		self.view.add_subview(self.line_3)
		self.view.add_subview(self.func_text)
		self.view.add_subview(self.func_descr_text)

		self.on_button.add_target(self.turn_on, event=UIEvent.press, arg=None)

		self.view.add_subview(self.on_button)
		self.view.add_subview(self.on_button_text)

		self.off_button.add_target(self.turn_off, event=UIEvent.press, arg=None)

		self.view.add_subview(self.off_button)
		self.view.add_subview(self.off_button_text)
		super().view_did_load()


window = UIWindow(
	view_controller=MainViewController,
	width=1920,
	height=1080,
	title="demo"
)

application = UIApplication(
	[window]
)

os.system("xrandr --output Virtual-1 --mode 1920x1080 --rate 60")
application.run()
