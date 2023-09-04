import os
import json
import requests
import shutil
import uuid
import random
import base64
import hashlib
import cv2
from customtkinter import CTk, CTkImage, CTkLabel, CTkButton, CTkEntry, CTkToplevel, filedialog
from PIL import Image, ImageTk, ImageSequence

class FileMetadataHandler:
	def __init__(self, json_file_path, error_label_widget):
		self.json_file_path = json_file_path
		self.error_label_widget = error_label_widget

	def read_json(self):
		with open(self.json_file_path, "r") as fp:
			return json.load(fp)

	def is_json_well_formed(self, data=None):
			if data:
				try:
					json.dumps(data)
				except (TypeError, OverflowError):
					return False
			try:
				self.read_json()
				return True
			except json.JSONDecodeError:
				return False

	def write_json(self, data):
		with open(self.json_file_path, "w") as fp:
			json.dump(data, fp, indent=2)

	def modify_json(self, file, tags):
		name = os.path.splitext(os.path.basename(file))[0]
		_, ext = os.path.splitext(file)
		ext = ext[1:]
		new_data = {"id": name, "tags": tags, "extension": ext}
		if not self.is_json_well_formed(new_data):
			self.show_error("Data to be added or JSON data in the file is not well-formed.")
		data = self.read_json()
		rnd_index = random.randint(0, len(data))
		data.insert(rnd_index, new_data)
		self.write_json(data)

	def show_error(self, message):
		self.error_label_widget.configure(bg_color="transparent")
		self.error_label_widget.configure(text=message, fg_color="red")
		raise Exception(message)

	def move_media_file(self, file: str, parent_dir_name: str) -> str:
		file_name = uuid.uuid4()
		_, ext = os.path.splitext(file)
		ext = ext[1:].lower()
		
		public_dir = None
		for root, dirs, _ in os.walk('./'):
			if 'public' in dirs:
				public_dir = os.path.join(root, parent_dir_name, 'public')
				break
		if public_dir is None:
			self.show_error("Could not find the 'public' directory.")
		
		new_file = os.path.join(public_dir, f"{file_name}.{ext}")
		shutil.move(file, new_file)
		print("Moved file:", new_file)
		return new_file

class InputValidator:

	def __init__(self, entry_widget, error_label_widget):
		self.entry_widget = entry_widget
		self.error_label_widget = error_label_widget

	def validate_entry(self):
		text = self.entry_widget.get().strip()
		self.entry_widget.configure(bg_color="transparent")
		self.error_label_widget.configure(text="")
		validation_checks = [
			self.is_empty,
			self.has_invalid_characters,
			self.has_special_characters,
			self.has_only_commas_or_spaces,
			self.has_invalid_commas,
			self.is_short_or_duplicate
		]
		for check in validation_checks:
			if check(text):
				return False
		return True

	def is_empty(self, text):
		if not text:
			self.show_error("Invalid input. Empty text is not allowed.")
			return True
		return False

	def has_invalid_characters(self, text):
		if not all(c.isalpha() or c.isspace() or c == ',' for c in text):
			self.show_error("Invalid characters. Only letters, spaces, and commas are allowed.")
			return True
		return False

	def has_special_characters(self, text):
		if not all(ord(c) < 128 for c in text):
			self.show_error("Invalid input. Accentuated, hyphenated, or special characters are not allowed.")
			return True
		return False

	def has_only_commas_or_spaces(self, text):
		clean_text = "".join(text.split())
		if clean_text == "," or clean_text.replace(',', '') == "":
			self.show_error("Invalid input. Only commas and spaces are not allowed.")
			return True
		return False

	def has_invalid_commas(self, text):
		clean_text = "".join(text.split())
		if clean_text.startswith(",") or clean_text.endswith(",") or any(len(part) == 0 for part in clean_text.split(',')):
			self.show_error("Invalid input. Leading or trailing commas or multiple consecutive commas are not allowed.")
			return True
		return False

	def is_short_or_duplicate(self, text):
		strings = [string.strip().lower() for string in text.split(',') if string.strip()]
		if len(strings) < 2 or any(len(string) < 2 for string in strings) or len(strings) != len(set(strings)):
			self.show_error("Invalid input. At least two unique tags of minimum two characters are required.")
			return True
		return False

	def show_error(self, message):
		self.entry_widget.configure(bg_color="transparent")
		self.error_label_widget.configure(text=message, fg_color="red")

class GitHubAPI:
	def __init__(self, token, owner, repo, fork_owner):
		self.headers = {
			"Authorization": f"token {token}",
			"Accept": "application/vnd.github.v3+json"
		}
		self.base_url = f"https://api.github.com/repos/{owner}/{repo}"
		self.fork_owner = fork_owner

	def create_pull_request(self, branch_name, title):
		url = f"{self.base_url}/pulls"
		head = f"{self.fork_owner}:{branch_name}"
		base = "master"
		data = {
			'head': head,
			'base': base,
			'title': title,
		}
		response = requests.post(url, headers=self.headers, json=data)
		if response.status_code == 201:
			print('Pull request created successfully!')
			print('URL:', response.json()['html_url'])
		else:
			print('Error:', response.status_code)
			print(response.text)
			if response.status_code == 422:
				print("Possible reason: Trying to create a PR with the same branch as source and destination.")

class MediaApp:
	def __init__(self, root):
		self.initialize_variables(root)
		self.initialize_ui()
		json_path = os.path.join(self.base_dir, 'src', 'pages', 'pepe.json')
		self.json_handler = FileMetadataHandler(json_path, self.error_label)
		self.input_validator = InputValidator(self.entry, self.error_label)
		self.github_api = GitHubAPI(self.token, "kekorder", "pepe.town", "Oriza")


	def initialize_variables(self, root):
		print("Initializing variables")
		os.system("gituser personal")
		self.root = root
		self.media_files = []
		self.token = os.environ.get('PEPETOWN_TOKEN')
		self.base_dir = os.path.dirname(os.path.abspath(__file__))
		self.index = 0
		self.last_width = 0
		self.last_height = 0
		self.is_video = False
		self.cap = None
		self.current_frame = None
		self.is_gif = False
		self.original_gif_frames = []
		self.gif_frames = []
		self.current_gif_frame_index = 0

	def initialize_ui(self):
		print("Initializing UI")
		self.label = CTkLabel(self.root, width=512, height=512, corner_radius=16, text="", fg_color="transparent")
		self.label.grid(row=0, column=0, columnspan=3, sticky='nsew')

		self.button_select_dir = CTkButton(self.root, text="Select Media Directory", command=self.select_directory, height=16, corner_radius=10)
		self.button_select_dir.grid(row=2, column=1)
		
		self.entry = CTkEntry(self.root, height=16, corner_radius=10, border_color="#3E9E36")
		self.entry.grid(row=1, column=1)
		self.entry.bind("<Return>", self.process_entry)
		self.entry.grid_remove()
		
		self.button_print = CTkButton(self.root, text="Set Tags", command=self.process_entry, height=16, corner_radius=10, fg_color="#3E9E36", hover_color="#2B6F26")
		self.button_print.grid(row=2, column=1)
		self.button_print.grid_remove()
		
		self.button_prev = CTkButton(self.root, text="Previous", command=self.show_prev, height=16, corner_radius=10, fg_color="white", text_color="black", hover_color="#D3D3D3")
		self.button_prev.grid(row=2, column=2)
		self.button_prev.grid_remove()
		
		self.button_next = CTkButton(self.root, text="Next", command=self.show_next, height=16, corner_radius=10, fg_color="white", text_color="black", hover_color="#D3D3D3")
		self.button_next.grid(row=1, column=2)
		self.button_next.grid_remove()
		
		self.error_label = CTkLabel(self.root, text="", fg_color="transparent", height=16, corner_radius=10)
		self.error_label.grid(row=3, column=0, columnspan=3)
  
		self.button_create_pr = CTkButton(self.root, text="Create PR", command=self.create_pr, height=16, corner_radius=10)
		self.button_create_pr.grid(row=2, column=0)
		self.button_create_pr.grid_remove()

		self.root.grid_columnconfigure(0, weight=1)
		self.root.grid_columnconfigure(1, weight=1)
		self.root.grid_columnconfigure(2, weight=1)
		self.root.grid_rowconfigure(0, weight=1)
		self.root.bind("<Configure>", self.resize)

	def create_pr(self):
		token = os.environ.get('PEPETOWN_TOKEN')
		if not token:
			self.show_error("Token not set in environment variables!")
			return
		branch_name = "images"  # you can generate unique names if needed
		os.system(f"git checkout -b {branch_name}")
		os.system("git add *")
		os.system('git commit -m "testing stuff"')
		os.system(f"git push origin {branch_name}")	
		self.github_api.create_pull_request(f"kekorder:{branch_name}", "PR from script")

	def select_directory(self):
		current_directory = os.getcwd()
		folder_path = filedialog.askdirectory(initialdir=current_directory, title="Select Your Media Files Directory")
		print("Selected folder:", folder_path)
		if folder_path:
			self.media_files = [
				os.path.join(folder_path, f)
				for f in os.listdir(folder_path)
				if f.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'mp4', 'avi'))
			]
			if self.media_files:
				self.button_select_dir.grid(row=1, column=0)
				self.button_prev.grid()
				self.button_next.grid()
				self.button_print.grid()
				self.entry.grid()
				self.index = 0
				self.load_current_file()
				self.button_create_pr.grid()
			else:
				self.button_prev.grid_remove()
				self.button_next.grid_remove()
				self.button_print.grid_remove()
				self.show_error("No media files in selected directory")
		else:
			self.show_error("No directory selected")
		self.root.focus_force()

	def cleanup(self):
		self.error_label.configure(text="", fg_color="transparent")
		self.close_video_if_needed()

		self.gif_frames = []
		self.gif_frame_index = 0

		self.label.configure(image=None)
		self.current_frame = None

	def show_error(self, message):
		self.error_label.configure(bg_color="transparent")
		self.error_label.configure(text=message, fg_color="red")

	def load_current_file(self):
		self.cleanup()
		# print(f"Loading file {self.media_files[self.index]} with index {self.index}")
		file_ext = self.get_file_extension()
		if file_ext in ['mp4', 'avi']:
			self.load_video()
		else:
			self.load_image()
		self.update_label()

	def get_file_extension(self):
		return self.media_files[self.index].split('.')[-1].lower()

	def load_video(self):
		self.is_video = True
		self.cap = cv2.VideoCapture(self.media_files[self.index])
		self.play_video()
 
	def load_image(self):
		self.is_video = False
		self.image = Image.open(self.media_files[self.index])
		if self.get_file_extension() == 'gif':
			self.is_gif = True
			self.gif_frames = [frame.copy() for frame in ImageSequence.Iterator(self.image)]
			self.current_gif_frame_index = 0
		else:
			self.is_gif = False
			self.current_frame = ImageTk.PhotoImage(self.image)
		self.update_label()

	def update_label(self):
		self.label.configure(image='')
		if self.is_video:
			self.label.configure(image=self.current_frame)
		elif self.is_gif:
			self.current_frame = ImageTk.PhotoImage(self.gif_frames[self.current_gif_frame_index])
			self.label.configure(image=self.current_frame)
			self.current_gif_frame_index = (self.current_gif_frame_index + 1) % len(self.gif_frames)
			self.root.after(100, self.update_label)
		else:
			img = self.get_resized_image()
			self.current_frame = ImageTk.PhotoImage(img)
			self.label.configure(image=self.current_frame)

	def process_entry(self, event=None):
		if self.input_validator.validate_entry():
			self.process_tags_and_show_next()

	def process_tags_and_show_next(self):
		text = self.entry.get().strip().lower()
		tags = [tag.strip() for tag in text.split(',') if tag.strip()]
		self.process_file(tags)
		self.entry.delete(0, 'end')
		self.close_video_if_needed()
		self.show_next()
		# if (self.index + 1) % 10 == 0:
			# token = os.environ.get('PEPETOWN_TOKEN')
			# self.github_api.create_pull_request("kekorder", "pepe.town", "main", "main", "Added 10 new images", "Added 10 new images", token)

	def process_file(self, tags):
		self.close_video_if_needed()
		new_file_path = FileMetadataHandler.move_media_file(self.json_handler, self.media_files[self.index], self.base_dir)
		self.json_handler.modify_json(new_file_path, tags)
		print(f"Moved: {new_file_path}, Modified JSON: {tags}")
 
	def show_next(self):
		self.close_video_if_needed()
		self.index += 1
		if self.index == len(self.media_files):
			self.index = 0
		self.load_current_file()
 
	def show_prev(self):
		self.close_video_if_needed()
		self.index -= 1
		if self.index < 0:
			self.index = len(self.media_files) - 1
		self.load_current_file()
 
	def close_video_if_needed(self):
		if self.cap:
			self.root.after_cancel(self.play_video_id)
			self.cap.release()
			self.cap = None
			self.is_video = False

	def play_video(self):
		"""Play the video file."""
		ret, frame = self.cap.read()
		if ret:
			cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
			img = Image.fromarray(cv2image)
			self.current_frame = ImageTk.PhotoImage(self.get_resized_image(img))
			self.update_label()
			self.play_video_id = self.root.after(10, self.play_video)
		else:
			self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
			self.play_video()

	def get_resized_image(self, img=None):
		"""Get a resized image according to the label dimensions."""
		if img is None:
			img = self.gif_frames[self.current_gif_frame_index] if self.is_gif else self.image
		return self.resize_image_to_fit_label(img)

	def resize_image_to_fit_label(self, img):
		"""Resize the image maintaining the aspect ratio to fit the label."""
		label_width, label_height = self.label.winfo_width(), self.label.winfo_height()
		return self.resize_image(img, label_width, label_height)

	@staticmethod
	def resize_image(img, width, height):
		"""Resize an image maintaining the aspect ratio."""
		img_width, img_height = img.size
		aspect_ratio = img_width / img_height

		if img_width > img_height:
			new_width = width
			new_height = int(width / aspect_ratio)
		else:
			new_height = height
			new_width = int(height * aspect_ratio)

		return img.resize((new_width, new_height), Image.LANCZOS)

	def resize(self, event=None):
		"""Resize the current frame when the window size changes."""
		if not self.is_video and self.current_frame:
			label_width, label_height = self.label.winfo_width(), self.label.winfo_height()

			if self.is_significant_resize(label_width, label_height):
				self.last_width = label_width
				self.last_height = label_height
				self.update_resized_frames_and_label()

	def is_significant_resize(self, width, height):
		"""Check if the resize is significant enough to update the image."""
		return abs(width - self.last_width) > 10 or abs(height - self.last_height) > 10

	def update_resized_frames_and_label(self):
		"""Update resized frames and the display label."""
		if self.is_gif:
			self.resize_gif_frames()
		self.update_label()

	def resize_gif_frames(self):
		"""Resize all frames of the gif image."""
		label_width, label_height = self.label.winfo_width(), self.label.winfo_height()
		self.gif_frames = [self.resize_image(frame, label_width, label_height) for frame in self.gif_frames]

if __name__ == "__main__":
	os.system("clear")
	root = CTk()
	root.title("Frentegration Tool 🐸")
	app = MediaApp(root)
	root.mainloop()
