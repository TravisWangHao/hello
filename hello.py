import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import time
import threading
import ctypes

# 1. 启用 Windows 高 DPI 感知，防止屏幕缩放 (125%/150%) 导致坐标错位或点击偏离
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# 2. 导入 pyautogui 作为备选与辅助，并关闭其导致卡顿与崩溃的内置机制
try:
    import pyautogui
    pyautogui.FAILSAFE = False  # 彻底关闭角落故障安全（原代码移动到屏幕边缘直接报错导致停止）
    pyautogui.PAUSE = 0        # 移除每次动作默认的 0.1 秒强制延迟
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False

# 3. 尝试导入 keyboard 库支持全局热键
try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False

# --- Windows 底层 Win32 API 鼠标控制 (极速、稳定、不漏点、不崩溃) ---
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

def win32_get_mouse_pos():
    """获取当前鼠标全局绝对坐标"""
    try:
        pt = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y
    except Exception:
        if HAS_PYAUTOGUI:
            return pyautogui.position()
        return 0, 0

def win32_set_mouse_pos(x, y):
    """设置鼠标全局坐标"""
    try:
        ctypes.windll.user32.SetCursorPos(int(x), int(y))
    except Exception:
        if HAS_PYAUTOGUI:
            pyautogui.moveTo(x, y)

def win32_click(button='left', click_type='single'):
    """
    底层模拟鼠标点击：
    避免了 PyAutoGUI 带来的 FailSafeException 和内置 sleep 锁死问题
    """
    try:
        if button == 'left':
            down_flag, up_flag = MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP
        elif button == 'right':
            down_flag, up_flag = MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP
        else:
            down_flag, up_flag = MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP

        # 触发按下与释放
        ctypes.windll.user32.mouse_event(down_flag, 0, 0, 0, 0)
        ctypes.windll.user32.mouse_event(up_flag, 0, 0, 0, 0)

        # 双击
        if click_type == 'double':
            time.sleep(0.02)
            ctypes.windll.user32.mouse_event(down_flag, 0, 0, 0, 0)
            ctypes.windll.user32.mouse_event(up_flag, 0, 0, 0, 0)
    except Exception as e:
        if HAS_PYAUTOGUI:
            if click_type == 'double':
                pyautogui.doubleClick(button=button)
            else:
                pyautogui.click(button=button)
        else:
            raise e

def is_admin():
    """检测当前是否具有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("自动点击器 (Auto Clicker) - 增强稳定版")
        self.root.geometry("450x460")
        self.root.resizable(False, False)

        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam')

        self.is_running = False
        self.click_thread = None
        self.stop_event = threading.Event()
        self.total_clicks = 0

        # UI 变量
        self.var_x = tk.StringVar(value="0")
        self.var_y = tk.StringVar(value="0")
        self.var_interval = tk.StringVar(value="100")  # 默认 100ms
        self.var_unit = tk.StringVar(value="毫秒 (ms)")
        self.var_duration = tk.StringVar(value="0")
        self.var_button = tk.StringVar(value="左键")
        self.var_click_type = tk.StringVar(value="单击")
        self.var_topmost = tk.BooleanVar(value=True)
        self.var_current_pos = tk.BooleanVar(value=True)  # 默认点击当前鼠标位置
        self.var_return_pos = tk.BooleanVar(value=False)

        self._init_ui()
        self._toggle_topmost()
        self._toggle_pos_entries()

        # 注册全局热键 F8
        if HAS_KEYBOARD:
            try:
                keyboard.add_hotkey('F8', self.toggle_clicking)
            except Exception as e:
                print(f"注册热键失败: {e}")

    def _init_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. 位置设置
        pos_frame = ttk.LabelFrame(main_frame, text="点击位置", padding="8")
        pos_frame.pack(fill=tk.X, pady=3)

        ttk.Checkbutton(
            pos_frame, text="跟随鼠标（在当前鼠标所在位置点击）",
            variable=self.var_current_pos, command=self._toggle_pos_entries
        ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 4))

        ttk.Label(pos_frame, text="固定 X:").grid(row=1, column=0, padx=4, pady=3, sticky="e")
        self.entry_x = ttk.Entry(pos_frame, textvariable=self.var_x, width=8)
        self.entry_x.grid(row=1, column=1, padx=4, pady=3, sticky="w")

        ttk.Label(pos_frame, text="固定 Y:").grid(row=1, column=2, padx=4, pady=3, sticky="e")
        self.entry_y = ttk.Entry(pos_frame, textvariable=self.var_y, width=8)
        self.entry_y.grid(row=1, column=3, padx=4, pady=3, sticky="w")

        self.btn_get_pos = ttk.Button(pos_frame, text="抓取固定坐标 (3秒延迟倒计时)", command=self.start_get_position)
        self.btn_get_pos.grid(row=2, column=0, columnspan=4, pady=(4, 2), sticky="ew")

        # 2. 点击参数
        param_frame = ttk.LabelFrame(main_frame, text="点击设置", padding="8")
        param_frame.pack(fill=tk.X, pady=4)

        # 鼠标按键与类型
        ttk.Label(param_frame, text="按键:").grid(row=0, column=0, padx=4, pady=3, sticky="e")
        btn_combo = ttk.Combobox(param_frame, textvariable=self.var_button, values=["左键", "右键", "中键"], width=6, state="readonly")
        btn_combo.grid(row=0, column=1, padx=4, pady=3, sticky="w")

        ttk.Label(param_frame, text="方式:").grid(row=0, column=2, padx=4, pady=3, sticky="e")
        type_combo = ttk.Combobox(param_frame, textvariable=self.var_click_type, values=["单击", "双击"], width=6, state="readonly")
        type_combo.grid(row=0, column=3, padx=4, pady=3, sticky="w")

        # 间隔时间与单位
        ttk.Label(param_frame, text="间隔:").grid(row=1, column=0, padx=4, pady=3, sticky="e")
        self.entry_interval = ttk.Entry(param_frame, textvariable=self.var_interval, width=8)
        self.entry_interval.grid(row=1, column=1, padx=4, pady=3, sticky="w")

        unit_combo = ttk.Combobox(param_frame, textvariable=self.var_unit, values=["毫秒 (ms)", "秒 (s)"], width=9, state="readonly")
        unit_combo.grid(row=1, column=2, columnspan=2, padx=4, pady=3, sticky="w")

        # 定时停止
        ttk.Label(param_frame, text="定时:").grid(row=2, column=0, padx=4, pady=3, sticky="e")
        self.entry_duration = ttk.Entry(param_frame, textvariable=self.var_duration, width=8)
        self.entry_duration.grid(row=2, column=1, padx=4, pady=3, sticky="w")
        ttk.Label(param_frame, text="分钟 (0为一直点)").grid(row=2, column=2, columnspan=2, padx=4, pady=3, sticky="w")

        # 3. 辅助选项
        opt_frame = ttk.Frame(main_frame)
        opt_frame.pack(fill=tk.X, pady=2)
        ttk.Checkbutton(opt_frame, text="固定坐标点击后拉回原鼠标位置", variable=self.var_return_pos).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(opt_frame, text="窗口置顶", variable=self.var_topmost, command=self._toggle_topmost).pack(side=tk.RIGHT, padx=5)

        # 4. 控制按钮
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=8)

        self.btn_start = tk.Button(
            control_frame, text="▶ 开始点击 (F8)", command=self.start_clicking,
            bg="#a5d6a7", activebackground="#81c784", font=("微软雅黑", 10, "bold"), relief="groove"
        )
        self.btn_start.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=4, ipady=6)

        self.btn_stop = tk.Button(
            control_frame, text="⏹ 停止点击 (F8)", command=self.stop_clicking, state=tk.DISABLED,
            bg="#ef9a9a", activebackground="#e57373", font=("微软雅黑", 10, "bold"), relief="groove"
        )
        self.btn_stop.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=4, ipady=6)

        # 5. 状态栏与提示
        status_box = ttk.Frame(main_frame)
        status_box.pack(side=tk.BOTTOM, fill=tk.X, pady=2)

        self.status_var = tk.StringVar(value="状态: 就绪 (按 F8 或点击按钮开始)")
        self.lbl_status = ttk.Label(status_box, textvariable=self.status_var, foreground="#1565c0", font=("微软雅黑", 9, "bold"))
        self.lbl_status.pack(anchor="w")

        # 管理员权限提示
        admin_text = "【已获得管理员权限】" if is_admin() else "【提示: 如需点击游戏或提权窗口，请右键管理员身份运行】"
        admin_color = "#388e3c" if is_admin() else "#757575"
        self.lbl_admin = ttk.Label(status_box, text=admin_text, foreground=admin_color, font=("微软雅黑", 8))
        self.lbl_admin.pack(anchor="w", pady=(2, 0))

    def _toggle_topmost(self):
        self.root.attributes('-topmost', self.var_topmost.get())

    def _toggle_pos_entries(self):
        is_fixed = not self.var_current_pos.get()
        state = tk.NORMAL if is_fixed else tk.DISABLED
        self.entry_x.config(state=state)
        self.entry_y.config(state=state)
        self.btn_get_pos.config(state=state)

    def toggle_clicking(self):
        if self.is_running:
            self.root.after(0, self.stop_clicking)
        else:
            self.root.after(0, self.start_clicking)

    def start_get_position(self):
        self.btn_get_pos.config(state=tk.DISABLED)
        self.btn_start.config(state=tk.DISABLED)
        threading.Thread(target=self._get_position_thread, daemon=True).start()

    def _get_position_thread(self):
        for i in range(3, 0, -1):
            self.root.after(0, lambda sec=i: self.status_var.set(f"请在 {sec} 秒内移动鼠标到目标位置..."))
            time.sleep(1)
        x, y = win32_get_mouse_pos()
        self.root.after(0, self._update_position_gui, x, y)

    def _update_position_gui(self, x, y):
        self.var_x.set(str(x))
        self.var_y.set(str(y))
        self.status_var.set(f"获取坐标成功! X: {x}, Y: {y}")
        self.btn_get_pos.config(state=tk.NORMAL)
        self.btn_start.config(state=tk.NORMAL)

    def start_clicking(self):
        if self.is_running:
            return

        try:
            raw_interval = float(self.var_interval.get())
            if raw_interval <= 0:
                raise ValueError("点击间隔必须大于 0")

            # 单位换算为秒
            if "毫秒" in self.var_unit.get():
                interval_sec = raw_interval / 1000.0
            else:
                interval_sec = raw_interval

            duration_minutes = float(self.var_duration.get())
            x = int(self.var_x.get())
            y = int(self.var_y.get())
        except ValueError as e:
            messagebox.showerror("输入错误", f"请输入合法的数字参数！\n{e}")
            return

        # 按键映射
        btn_map = {"左键": "left", "右键": "right", "中键": "middle"}
        type_map = {"单击": "single", "双击": "double"}
        btn_choice = btn_map.get(self.var_button.get(), "left")
        type_choice = type_map.get(self.var_click_type.get(), "single")

        self.is_running = True
        self.stop_event.clear()
        self.total_clicks = 0

        self.btn_start.config(state=tk.DISABLED)
        self.btn_get_pos.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)

        mode_text = "当前鼠标位置" if self.var_current_pos.get() else f"坐标({x}, {y})"
        self.status_var.set(f"运行中: {mode_text} | 间隔: {self.var_interval.get()}{self.var_unit.get()}")

        self.click_thread = threading.Thread(
            target=self._click_loop,
            args=(x, y, interval_sec, duration_minutes, btn_choice, type_choice),
            daemon=True
        )
        self.click_thread.start()

    def stop_clicking(self):
        if not self.is_running:
            return
        self.is_running = False
        self.stop_event.set()

        self.btn_start.config(state=tk.NORMAL)
        if not self.var_current_pos.get():
            self.btn_get_pos.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.status_var.set(f"已停止 | 本次共点击: {self.total_clicks} 次")

    def _click_loop(self, x, y, interval_sec, duration_minutes, button, click_type):
        start_time = time.time()
        duration_seconds = duration_minutes * 60
        use_current = self.var_current_pos.get()
        return_pos = self.var_return_pos.get()
        last_ui_update = 0.0

        while self.is_running and not self.stop_event.is_set():
            try:
                # 1. 检查是否达到定时停止时间
                if duration_seconds > 0:
                    elapsed = time.time() - start_time
                    if elapsed >= duration_seconds:
                        self.root.after(0, lambda: self.status_var.set(f"定时完成，已自动停止 (共点击 {self.total_clicks} 次)"))
                        break

                # 2. 执行点击
                if use_current:
                    win32_click(button, click_type)
                else:
                    cur_x, cur_y = win32_get_mouse_pos()
                    win32_set_mouse_pos(x, y)
                    win32_click(button, click_type)
                    if return_pos:
                        win32_set_mouse_pos(cur_x, cur_y)

                self.total_clicks += 1

                # 3. 节流更新 UI，防止极低间隔高频触发导致 GUI 消息队列卡死
                now = time.time()
                if now - last_ui_update >= 0.25:
                    last_ui_update = now
                    c = self.total_clicks
                    if duration_seconds > 0:
                        rem = max(0, int(duration_seconds - (now - start_time)))
                        self.root.after(0, lambda count=c, r=rem: self.status_var.set(f"运行中 | 已点击: {count} 次 | 剩余: {r} 秒"))
                    else:
                        self.root.after(0, lambda count=c: self.status_var.set(f"运行中 | 已点击: {count} 次"))

                # 4. 精确延迟等待
                if interval_sec > 0:
                    if self.stop_event.wait(interval_sec):
                        break
                else:
                    time.sleep(0.001)

            except Exception as e:
                err_str = str(e)
                print(f"点击发生异常: {err_str}")
                self.root.after(0, lambda err=err_str: self.status_var.set(f"异常终止: {err}"))
                break

        # 循环自然结束或异常跳出的状态收尾
        if self.is_running:
            self.root.after(0, self.stop_clicking)


if __name__ == "__main__":
    root = tk.Tk()
    app = AutoClickerApp(root)
    root.mainloop()
