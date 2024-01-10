# Импортируем нужные для нашего проекта библиотеки 
# Импортируем настройки системы
import sys
import os
# Импортируем модули из основной библиотеки нашего проекта PyQt5
from PyQt5.QtWidgets import (
    QApplication, 
    QMainWindow,
    QFileDialog, 
    QMenu, 
    QAction,
    QSpinBox,
    QToolBar, 
    QColorDialog, 
    QUndoCommand,
    QUndoStack, 
    QStatusBar,
    QPushButton,
    QWidget,
    QVBoxLayout,
    QMessageBox
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import *
from PyQt5.QtGui import *
# Библиотека для получения информации о размере экрана
from screeninfo import get_monitors
# Импортируем модуль для конвертации изображения в PIL
from PIL import ImageQt, Image
# Импортируем Pillow для обработки фотографий
from PIL import (
    ImageFilter, 
    ImageOps
)
# Импортируем библиотеку рандом для функции рисования граффити
import random


# Задаем директорию для файлов нашего фотошопа
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# Список цветов для виджетов цвета который мы потом создадим
COLORS = [
'#000000', '#141923', '#414168', '#3a7fa7', '#35e3e3', '#8fd970', '#5ebb49',
'#458352', '#dcd37b', '#fffee5', '#ffd035', '#cc9245', '#a15c3e', '#a42f3b',
'#f45b7a', '#c24998', '#81588d', '#bcb0c2', '#ffffff',
]


# Создаем класс кнопки цвета
class QPaletteButton(QPushButton):
    def __init__(self, color):
        super().__init__()
        self.setFixedSize(QSize(24,24))
        self.color = color
        self.setStyleSheet("background-color: %s;" % color)


# Создаем класс для создания функций redo/undo
class UndoCommand(QUndoCommand):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.mPrevImage = parent.image.copy()
        self.mCurrImage = parent.image.copy()

    def undo(self):
        self.mCurrImage = self.parent.image.copy()
        self.parent.image = self.mPrevImage
        self.parent.update()

    def redo(self):
        self.parent.image = self.mCurrImage
        self.parent.update()


# Обьявляем класс нашего главного приложения 
class Photoshop(QMainWindow): 
    def __init__(self): 
        super().__init__() 
        self.InitUI() 
        self.degree = 0
     
    # Функция описывающая дополнительные параметры
    def InitUI(self): 
        # Устанавливаем имя для нашего окна приложения 
        self.setWindowTitle("Paint")
        # Устанавливаем иконку для нашего окна приложения 
        self.setWindowIcon(QIcon(BASE_DIR + os.path.sep + "icons/palette.png"))
        
        # Устанавливаем размеры окна по максимальным для монитора
        self.monitor = get_monitors()[0]
        self.setGeometry(0, 0, self.monitor.width, self.monitor.height)

        # Открываем окно нашего приложения в максимально возможном размере 
        self.showMaximized()

        # Пишем стили для некоторых элементов нашего приложения
        self.setStyleSheet("""
            QToolBar {
                background: #eee;
                padding: 0px;
                border: 0px;
            }
                           
            QSpinBox {
                width: 40px;
                height: 24px;
                font-size: 16px;
            }
            """)
        
        # Отсутствие пути открытого файла
        self.open_adres = False

        # Создаем верхнее меню нашего фоторедактора 
        self.menu_bar = self.menuBar() 

        # Меню файла 
        self.file_menu_bar = QMenu("Файл", self) 
        self.menu_bar.addMenu(self.file_menu_bar)

        self.open_action = QAction("Открыть изображение", self)
        self.open_action.setShortcut("Ctrl+N")
        self.file_menu_bar.addAction(self.open_action)
        # Подключаем функцию открытия изображения
        self.open_action.triggered.connect(self.open_file_function)

        # Создаем действие для сохранения по тому же пути
        self.save_action = QAction("Сохранить", self)
        self.save_action.setShortcut("Ctrl+S")
        self.file_menu_bar.addAction(self.save_action)
        # Подключаем функцию сохранения старого изображения
        self.save_action.triggered.connect(self.save_file_function) 

        # Создаем действие для сохранения по новому пути
        self.save_as_action = QAction("Сохранить как", self) 
        self.save_as_action.setShortcut("Ctrl+Shift+S")
        self.file_menu_bar.addAction(self.save_as_action)
        # Подключаем функцию сохранения нового изображения
        self.save_as_action.triggered.connect(self.save_as_file_function) 
        
        # Создаем разделитель
        self.file_menu_bar.addSeparator()

        # Создаем действие очистки рабочей области
        self.clear_action = QAction("Очистить", self)
        self.file_menu_bar.addAction(self.clear_action)
        # Подключаем функцию очистки изображения
        self.clear_action.triggered.connect(self.clear_image)

        # Создаем действие возврата исходной картинки
        self.start_image = QAction("Вернуть исходное изображение")
        self.file_menu_bar.addAction(self.start_image)
        self.start_image.triggered.connect(self.startImagefunction)
        self.start_image.setEnabled(False)

        # Меню правки 
        self.edit_menu_bar = self.menu_bar.addMenu("Правка")

        # Настройки для redo/undo 
        self.mUndoStack = QUndoStack(self)
        self.mUndoStack.setUndoLimit(50)

        self.mUndoStack.canUndoChanged.connect(self.can_undo_changed)
        self.mUndoStack.canRedoChanged.connect(self.can_redo_changed)

        # Переменная показывающая открыто ли изображение
        self.flag_open_file = False

        self.actionUndo = QAction("Undo", self)
        self.actionUndo.setEnabled(False)
        self.edit_menu_bar.addAction(self.actionUndo)
        self.actionUndo.setShortcut("Ctrl+Z")
        self.actionUndo.triggered.connect(self.mUndoStack.undo)

        self.actionRedo = QAction("Redo", self)
        self.actionRedo.setEnabled(False)
        self.edit_menu_bar.addAction(self.actionRedo)
        self.actionRedo.setShortcut("Ctrl+Y")
        self.actionRedo.triggered.connect(self.mUndoStack.redo)
 
        # Меню инструментов 
        self.draw_menu = self.menu_bar.addMenu("Инструменты")

        # Блок кисти
        self.brush_menu = self.draw_menu.addMenu("Кисть")

        self.brush_on_action = QAction("Активировать кисть", self)
        self.brush_menu.addAction(self.brush_on_action)
        # Подключаем функцию для активации рисования
        self.brush_on_action.triggered.connect(self.brush_on_function)

        self.brush_off_action = QAction("Отключить кисть", self)
        self.brush_menu.addAction(self.brush_off_action)
        self.brush_off_action.triggered.connect(self.brush_off_function)

        self.color_pen_action = QAction("Цвет кисти", self)
        self.brush_menu.addAction(self.color_pen_action)
        # Подключаем функцию смены цвета кистиы
        self.color_pen_action.triggered.connect(self.setPenColor)

        # Блок прямой
        self.solid_menu = self.draw_menu.addMenu("Прямая")

        self.solid_on_action = QAction("Активировать рисование прямой")
        self.solid_menu.addAction(self.solid_on_action)
        self.solid_on_action.triggered.connect(self.solid_on_function)

        self.solid_off_action = QAction("Отключить рисование прямой")
        self.solid_menu.addAction(self.solid_off_action)
        self.solid_off_action.triggered.connect(self.solid_off_function)

        self.solid_color_action = QAction("Цвет прямой")
        self.solid_menu.addAction(self.solid_color_action)
        self.solid_color_action.triggered.connect(self.setPenColor)

        # Блок Ластика
        self.rubber_menu = self.draw_menu.addMenu("Ластик")

        self.rubber_on_action = QAction("Активировать ластик")
        self.rubber_menu.addAction(self.rubber_on_action)
        self.rubber_on_action.triggered.connect(self.rubber_on_function)

        self.rubber_off_action = QAction("Отключить ластик")
        self.rubber_menu.addAction(self.rubber_off_action)
        self.rubber_off_action.triggered.connect(self.rubber_off_function)

        # Блок Спрея
        self.graffiti_menu = self.draw_menu.addMenu("Спрей")

        self.graffiti_on_action = QAction("Активировать спрей")
        self.graffiti_menu.addAction(self.graffiti_on_action)
        self.graffiti_on_action.triggered.connect(self.graffiti_on_function)

        self.graffiti_off_action = QAction("Отключить спрей")
        self.graffiti_menu.addAction(self.graffiti_off_action)
        self.graffiti_off_action.triggered.connect(self.graffiti_off_function)

        self.graffiti_color_action = QAction("Цвет спрея")
        self.graffiti_menu.addAction(self.graffiti_color_action)
        self.graffiti_color_action.triggered.connect(self.setPenColor)

        #TODO: Сделать возможным выбрать размеры спрея... (радиуса, количсетва точек и тд)

        self.draw_menu.addSeparator()
        
        # Блок Круга
        self.circle_menu = self.draw_menu.addMenu("Окружность и круг")

        self.unfcircle_on_action = QAction("Активировать рисование окружности")
        self.circle_menu.addAction(self.unfcircle_on_action)
        self.unfcircle_on_action.triggered.connect(self.unf_circle_on_function)

        self.unfcircle_off_action = QAction("Отключить рисование окружности")
        self.circle_menu.addAction(self.unfcircle_off_action)
        self.unfcircle_off_action.triggered.connect(self.unf_circle_off_function)

        self.unfcircle_color_action = QAction("Цвет окружности")
        self.circle_menu.addAction(self.unfcircle_color_action)
        self.unfcircle_color_action.triggered.connect(self.setPenColor)

        self.circle_menu.addSeparator()

        self.circle_on_action = QAction("Активировать рисование круга")
        self.circle_menu.addAction(self.circle_on_action)
        self.circle_on_action.triggered.connect(self.circle_on_function)

        self.circle_off_action = QAction("Отключить рисование круга")
        self.circle_menu.addAction(self.circle_off_action)
        self.circle_off_action.triggered.connect(self.circle_off_function)

        self.circle_color_action = QAction("Цвет круга")
        self.circle_menu.addAction(self.circle_color_action)
        self.circle_color_action.triggered.connect(self.setPenColor)

        # Блок прямоугольника
        self.rectangle_menu = self.draw_menu.addMenu("Прямоугольник")

        self.unfrectangle_on_action = QAction("Активировать рисование незаполненного прямоугольника")
        self.rectangle_menu.addAction(self.unfrectangle_on_action)
        self.unfrectangle_on_action.triggered.connect(self.unfrectangle_on_function)

        self.unfrectangle_off_action = QAction("Отключить рисование незаполненного прямоугольника")
        self.rectangle_menu.addAction(self.unfrectangle_off_action)
        self.unfrectangle_off_action.triggered.connect(self.unfrectangle_off_function)

        self.unfrectangle_color_action = QAction("Цвет незаполненного прямоугольника")
        self.rectangle_menu.addAction(self.unfrectangle_color_action)
        self.unfrectangle_color_action.triggered.connect(self.setPenColor)

        self.rectangle_menu.addSeparator()

        self.rectangle_on_action = QAction("Активировать рисование заполненного прямоугольника")
        self.rectangle_menu.addAction(self.rectangle_on_action)
        self.rectangle_on_action.triggered.connect(self.rectangle_on_function)

        self.rectangle_off_action = QAction("Отключить рисование заполненного прямоугольника")
        self.rectangle_menu.addAction(self.rectangle_off_action)
        self.rectangle_off_action.triggered.connect(self.rectangle_off_function)

        self.rectangle_color_action = QAction("Цвет заполненного прямоугольника")
        self.rectangle_menu.addAction(self.rectangle_color_action)
        self.rectangle_color_action.triggered.connect(self.setPenColor)

        # Блок овала
        self.oval_menu = self.draw_menu.addMenu("Овал")

        self.unfoval_on_action = QAction("Активировать рисование незаполненного овала")
        self.oval_menu.addAction(self.unfoval_on_action)
        self.unfoval_on_action.triggered.connect(self.unfoval_on_function)

        self.unfoval_off_action = QAction("Отключить рисование незаполненного овала")
        self.oval_menu.addAction(self.unfoval_off_action)
        self.unfoval_off_action.triggered.connect(self.unfoval_off_function)

        self.unfoval_color_action = QAction("Цвет незаполненного овала")
        self.oval_menu.addAction(self.unfoval_color_action)
        self.unfoval_color_action.triggered.connect(self.setPenColor)

        self.oval_menu.addSeparator()

        self.oval_on_action = QAction("Активировать рисование заполненного овала")
        self.oval_menu.addAction(self.oval_on_action)
        self.oval_on_action.triggered.connect(self.oval_on_function)

        self.oval_off_action = QAction("Отключить рисование заполненного овала")
        self.oval_menu.addAction(self.oval_off_action)
        self.oval_off_action.triggered.connect(self.oval_off_function)

        self.oval_color_action = QAction("Цвет заполненного овала")
        self.oval_menu.addAction(self.oval_color_action)
        self.oval_color_action.triggered.connect(self.setPenColor)

        # Блок полуокружности
        self.hord_menu = self.draw_menu.addMenu("Полуокружность")

        self.hord_on_action = QAction("Активировать рисование полуокружности")
        self.hord_menu.addAction(self.hord_on_action)
        self.hord_on_action.triggered.connect(self.hord_on_function)

        self.hord_off_action = QAction("Отключить рисование полуокружности")
        self.hord_menu.addAction(self.hord_off_action)
        self.hord_off_action.triggered.connect(self.hord_off_function)

        self.hord_color_action = QAction("Цвет полуокружности")
        self.hord_menu.addAction(self.hord_color_action)
        self.hord_color_action.triggered.connect(self.setPenColor)

        # Блок дуги
        self.arc_menu = self.draw_menu.addMenu("Дуга")

        self.arc_on_action = QAction("Активировать рисование незаполненного овала")
        self.arc_menu.addAction(self.arc_on_action)
        self.arc_on_action.triggered.connect(self.arc_on_function)

        self.arc_off_action = QAction("Отключить рисование незаполненного овала")
        self.arc_menu.addAction(self.arc_off_action)
        self.arc_off_action.triggered.connect(self.arc_off_function)

        self.arc_color_action = QAction("Цвет незаполненного овала")
        self.arc_menu.addAction(self.arc_color_action)
        self.arc_color_action.triggered.connect(self.setPenColor)

        self.draw_menu.addSeparator()

        self.zalivka_action = QAction("Заливка фона", self)
        self.draw_menu.addAction(self.zalivka_action)
        # Подключаем функцию заливки
        self.zalivka_action.triggered.connect(self.zalivka_function) 

        # Меню фильтров 
        self.filters_bar = self.menu_bar.addMenu("Фильтры")

        self.black_action = QAction("Преобладание черного", self)
        self.filters_bar.addAction(self.black_action)
        # Подключаем функцию черного фильтра
        self.black_action.triggered.connect(self.black_filter) 

        self.white_action = QAction("Преобладание белого", self)
        self.filters_bar.addAction(self.white_action)
        # Подключаем функцию белого фильтра
        self.white_action.triggered.connect(self.white_filter)

        self.blur_action = QAction("Размытие", self)
        self.filters_bar.addAction(self.blur_action)
        # Подключаем функцию фильтра размытия
        self.blur_action.triggered.connect(self.blur_filter)
        
        self.detail_action = QAction("Резкость", self)
        self.filters_bar.addAction(self.detail_action)
        # Подключаем функцию фильтра резкости
        self.detail_action.triggered.connect(self.detail_function)
        
        self.volume_action = QAction("Объем", self)
        self.filters_bar.addAction(self.volume_action)
        # Подключаем функцию фильтра обьема
        self.volume_action.triggered.connect(self.volume_function)

        self.main_filter_action = QAction("Основные моменты", self)
        self.filters_bar.addAction(self.main_filter_action)
        # Подключаем функцию фильтра основных моментов
        self.main_filter_action.triggered.connect(self.main_filter_function)

        self.black_white_action = QAction("Черно-белое", self)
        self.filters_bar.addAction(self.black_white_action)
        self.black_white_action.triggered.connect(self.black_white_function)
        
        # Меню помощи 
        self.help_menu = self.menu_bar.addMenu("Помощь")

        # Добавляем блок информации о проекте
        # p.s. Когда то она там появится
        self.info_action = QAction("В разработке...", self)
        self.help_menu.addAction(self.info_action)

        # Блок инструментов
        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(32, 32))
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)
        self.setStatusBar(QStatusBar(self))

        # в toolbar'е
        self.open_file_button = QAction("Открыть", self)
        self.open_file_button.setIcon(QIcon(os.path.join(BASE_DIR + os.path.sep + 'icons/open.png')))
        self.toolbar.addAction(self.open_file_button)
        self.open_file_button.triggered.connect(self.open_file_function)

        self.save_file_button = QAction("Сохранить", self)
        self.save_file_button.setIcon(QIcon(os.path.join(BASE_DIR + os.path.sep + 'icons/save.png')))
        self.toolbar.addAction(self.save_file_button)
        self.save_file_button.triggered.connect(self.save_file_function)

        self.save_as_file_button = QAction("Сохранить как", self)
        self.save_as_file_button.setIcon(QIcon(os.path.join(BASE_DIR + os.path.sep + 'icons/save_as.png')))
        self.toolbar.addAction(self.save_as_file_button)
        self.save_as_file_button.triggered.connect(self.save_as_file_function)

        self.undo_button = QAction("Undo", self)
        self.undo_button.setIcon(QIcon(os.path.join(BASE_DIR + os.path.sep +  "icons/arrow-180.png")))
        self.toolbar.addAction(self.undo_button)
        self.undo_button.triggered.connect(self.mUndoStack.undo)

        self.redo_button = QAction("Redo", self)
        self.redo_button.setIcon(QIcon(BASE_DIR + os.path.sep + "icons/arrow.png"))
        self.toolbar.addAction(self.redo_button)
        self.redo_button.triggered.connect(self.mUndoStack.redo)

        self.background_button = QAction("Цвет заднего фона", self)
        self.background_button.setIcon(QIcon(BASE_DIR + os.path.sep + "icons/backgroundcolor.png"))
        self.toolbar.addAction(self.background_button)
        self.background_button.triggered.connect(self.zalivka_function)

        self.clean_button = QAction("Очистить", self)
        self.clean_button.setIcon(QIcon(BASE_DIR + os.path.sep + "icons/trash.png"))
        self.toolbar.addAction(self.clean_button)
        self.clean_button.triggered.connect(self.clear_image)

        self.toolbar.addSeparator()

        self.brush_button = QAction("Кисть", self)
        self.brush_button.setIcon(QIcon(BASE_DIR + os.path.sep + "icons/brush1.png"))
        # Позволяет сделать активным элемент
        self.brush_button.setCheckable(True)
        self.toolbar.addAction(self.brush_button)
        self.brush_button.triggered.connect(self.activate_brush_function)

        self.brush_color_shoose = QAction("Цвет инструмента", self)
        self.brush_color_shoose.setIcon(QIcon(BASE_DIR + os.path.sep + "icons/color.png"))
        self.toolbar.addAction(self.brush_color_shoose)
        self.brush_color_shoose.triggered.connect(self.setPenColor)

        self.brush_size_shoose = QSpinBox(self)
        # В приведенном ниже коде вы устанавливаете свойство счетчика в значение потому что, 
        # если этот виджет получит фокус, то сочетания клавиш приложения не будут работать 
        # должным образом.focusPolicyQt.NoFocus
        # Запрещает менять QSpinBox 
        self.brush_size_shoose.setFocusPolicy(Qt.NoFocus)
        # Создаем предел для QSpinBox 
        self.brush_size_shoose.setMinimum(1)
        self.brush_size_shoose.setMaximum(100)
        # Убирает border 
        # self.brush_size_shoose.setFrame(False)
        # Используем addWidget так как QSpinBox является виджетом
        self.toolbar.addWidget(self.brush_size_shoose)
        self.brush_size_shoose.valueChanged.connect(self.setPenSize)

        self.solid_line_button = QAction("Прямая", self)
        self.solid_line_button.setIcon(QIcon(BASE_DIR + os.path.sep + "icons/line.png"))
        # Позволяет сделать активным элемент
        self.solid_line_button.setCheckable(True)
        self.toolbar.addAction(self.solid_line_button)
        self.solid_line_button.triggered.connect(self.activate_solid_function)

        self.rubber_action_button = QAction("Ластик", self)
        self.rubber_action_button.setIcon(QIcon(BASE_DIR + os.path.sep + "icons/rubber.png"))
        self.toolbar.addAction(self.rubber_action_button)
        self.rubber_action_button.setCheckable(True)
        self.rubber_action_button.triggered.connect(self.activate_rubber_function)

        self.graffiti_button = QAction("Граффити", self)
        self.graffiti_button.setIcon(QIcon(BASE_DIR + os.path.sep + "icons/graffiti.png"))
        self.graffiti_button.setCheckable(True)
        self.toolbar.addAction(self.graffiti_button)
        self.graffiti_button.triggered.connect(self.activate_graffiti_function)

        self.toolbar.addSeparator()

        self.circle_button = QAction("Заполненный руг", self)
        self.circle_button.setIcon(QIcon(BASE_DIR + os.path.sep + "icons/filledcircle.png"))
        self.circle_button.setCheckable(True)
        self.toolbar.addAction(self.circle_button)
        self.circle_button.triggered.connect(self.activate_circle_function)

        self.unfilled_circle_button = QAction("Окружность", self)
        self.unfilled_circle_button.setIcon(QIcon(BASE_DIR + os.path.sep + "icons/circle.png"))
        self.unfilled_circle_button.setCheckable(True)
        self.toolbar.addAction(self.unfilled_circle_button)
        self.unfilled_circle_button.triggered.connect(self.activate_unf_circle_function)

        self.filled_rectangle_button = QAction("Заполненный прямоугольник", self)
        self.filled_rectangle_button.setIcon(QIcon(BASE_DIR + os.path.sep + "icons/filledrectangle.png"))
        self.filled_rectangle_button.setCheckable(True)
        self.toolbar.addAction(self.filled_rectangle_button)
        self.filled_rectangle_button.triggered.connect(self.activate_rectangle_function)
        
        self.unfilled_rectangle_button = QAction("Пустой прямоугольник", self)
        self.unfilled_rectangle_button.setIcon(QIcon(BASE_DIR + os.path.sep + "icons/rectangle.png"))
        self.unfilled_rectangle_button.setCheckable(True)
        self.toolbar.addAction(self.unfilled_rectangle_button)
        self.unfilled_rectangle_button.triggered.connect(self.activate_unfrectangle_function)

        self.filled_oval_button = QAction("Заполненный овал", self)
        self.filled_oval_button.setIcon(QIcon(BASE_DIR + os.path.sep + "icons/filledoval.png"))
        self.filled_oval_button.setCheckable(True)
        self.toolbar.addAction(self.filled_oval_button)
        self.filled_oval_button.triggered.connect(self.activate_oval_function)

        self.unfilled_oval_button = QAction("Пустой овал", self)
        self.unfilled_oval_button.setIcon(QIcon(BASE_DIR + os.path.sep + "icons/oval.png"))
        self.unfilled_oval_button.setCheckable(True)
        self.toolbar.addAction(self.unfilled_oval_button)
        self.unfilled_oval_button.triggered.connect(self.activate_unfoval_function)

        self.hord_button = QAction("Полуокружность", self)
        self.hord_button.setIcon(QIcon(BASE_DIR + os.path.sep + "icons/hord.png"))
        self.hord_button.setCheckable(True)
        self.toolbar.addAction(self.hord_button)
        self.hord_button.triggered.connect(self.activate_hord_function)

        self.arc_button = QAction("Дуга", self)
        self.arc_button.setIcon(QIcon(BASE_DIR + os.path.sep + "icons/arc.png"))
        self.arc_button.setCheckable(True)
        self.toolbar.addAction(self.arc_button)
        self.arc_button.triggered.connect(self.activate_arc_function)

        self.toolbar.addSeparator()

        self.rotate_left_button = QAction("Поворот влево", self)
        self.rotate_left_button.setIcon(QIcon(BASE_DIR + os.path.sep + "icons/rotate_left.png"))
        self.toolbar.addAction(self.rotate_left_button)
        self.rotate_left_button.triggered.connect(self.image_rotate_left)

        self.rotate_right_button = QAction("Поворот влево", self)
        self.rotate_right_button.setIcon(QIcon(BASE_DIR + os.path.sep + "icons/rotate_right.png"))
        self.toolbar.addAction(self.rotate_right_button)
        self.rotate_right_button.triggered.connect(self.image_rotate_right)

        self.mirrored_h_button = QAction("Зеркало по горизонтали", self)
        self.mirrored_h_button.setIcon(QIcon(BASE_DIR + os.path.sep + "icons/flip_horizontal.png"))
        self.toolbar.addAction(self.mirrored_h_button)
        self.mirrored_h_button.triggered.connect(self.image_mirror_horizontal)

        self.mirrored_v_button = QAction("Зеркало по вертикали", self)
        self.mirrored_v_button.setIcon(QIcon(BASE_DIR + os.path.sep + "icons/flip_vertical.png"))
        self.toolbar.addAction(self.mirrored_v_button)
        self.mirrored_v_button.triggered.connect(self.image_mirror_vertical)

        # Размещаем палитру цветов и создаем для этого вертикальную группу в которую поместим увета палитры
        palette = QVBoxLayout()
        # обьявляем функцию создания виджета палитры цветов
        self.add_palette_buttons(palette)
        # создаем виджет для палитры
        self.w = QWidget()
        # Устанавливаем виджету плаитры фиксированную высоту
        self.w.setFixedHeight(600)
        # устанавливаем группу в наш виджет
        self.w.setLayout(palette)
        self.setCentralWidget(self.w)

        # Флаг нажатой кнопки мыши
        self.is_pressed = False

        # Создание переменных для будущих рисующих объектов для каждого из инструментов
        self.drawingPath = False
        self.solidPath = False
        self.circlePath = False
        self.graffitiPath = False
        self.rubberPath = False
        self.circleunfPath = False
        self.rectanglePath = False
        self.rectangleunfPath = False
        self.ovalPath = False
        self.ovalunfPath = False
        self.hordPath = False
        self.arcPath = False

        # Настройки для рисования
        self.image = QImage(self.size(), QImage.Format_RGB32)
        self.bg_color = Qt.white
        self.image.fill(self.bg_color)
        self.myPenWidth = 1
        self.myPenColor = Qt.black

        # Настройки для произвольной линии
        self.lastPoint = QPoint()
        # Устанавливаем изначальный статус рисования кривой
        self.drawing_curved_line = False
        
        # Настройки для прямой линии
        self.last_position_solid = QPoint()
        self.current_position_solid = QPoint()
        # Устанавливаем изначальный статус рисования прямой
        self.drawing_solid_line = False
        
        # Настройки для граффити
        self.drawing_graffiti = False
        self.SPRAY_PARTICLES = 100
        self.SPRAY_DIAMETER = 10
        self.start_x = 0
        self.start_y = 0

        # Настройки для рисования круга
        self.drawing_circle = False
        self.drawing_unfcircle = False

        # Настройки для рисования прямоугольника
        self.drawing_rectangle = False
        self.drawing_unfrectangle = False
        
        # Настройка для овала
        self.drawing_oval = False
        self.drawing_unfoval = False
        
        # Настройки для полуокружности
        self.drawing_hord = False

        # Настройки для рисования дуги
        self.drawing_arc = False

        # Для фигур
        self.sx = 0
        self.sy = 0
        self.x1 = 0
        self.y1 = 0

        # Настройки для ластика
        self.drawing_rubber = False

        # Список инструментов
        self.list_instruments = [
            self.drawing_curved_line,
            self.drawing_solid_line,
            self.drawing_circle,
            self.drawing_graffiti,
            self.drawing_rubber,
            self.drawing_unfcircle,
            self.drawing_rectangle,
            self.drawing_unfrectangle,
            self.drawing_unfoval,
            self.drawing_oval,
            self.drawing_hord,
            self.drawing_arc
        ]

        # Список кнопок инструментов
        self.list_instruments_buttons = [
            self.brush_button,
            self.solid_line_button,
            self.circle_button,
            self.graffiti_button,
            self.rubber_action_button,
            self.unfilled_circle_button,
            self.filled_rectangle_button,
            self.unfilled_rectangle_button,
            self.filled_oval_button,
            self.unfilled_oval_button,
            self.hord_button,
            self.arc_button
        ]

        # Флаг сохранения изображения
        self.save_image_flag = False

    # Функция открытия фотографии 
    def open_file_function(self): 
        # Получаем изображение 
        self.open_adres, _ = QFileDialog.getOpenFileName(None, "Открыть изображение", ".", "Images (*.png *.jpg)") 
        # Создаем условие направленное на устранение проблемы прервания открытия файла для этого:
        if self.open_adres:
            self.rubber_action_button.setEnabled(False)
            # Делаем "канву" для нашей картинки 
            self.image = QPixmap(self.open_adres) 
            # Преобразуем QPixmap в QImage
            self.image = self.image.toImage()
            self.image = self.image.scaled(QSize(self.monitor.width, self.monitor.height))   
            self.update()
            self.save_image_flag = False

    # Функция сохранения получившегося изображения как нового файла
    def save_as_file_function(self):
        # Получаем путь для сохранения нового изображения
        self.save_adres, _ = QFileDialog.getSaveFileName(self, "Сохранить", ".", "Images (*.png *.jpg)")
        if self.save_adres:
            # Сохраняем наше новое изображение по извлеченному пути
            self.image.save(self.save_adres)
            self.save_image_flag = True
    
    # Функция сохранения получившегося изображения как старого файла
    def save_file_function(self):
        if self.open_adres:
            self.image.save(self.open_adres)
            self.save_image_flag = True

    # Функция очистки рабочей области
    def clear_image(self):
        self.path = QPainterPath()
        self.image = QImage(self.size(), QImage.Format_RGB32)
        self.bg_color = Qt.white
        self.image.fill(self.bg_color)
        self.update()
        self.start_image.setEnabled(False)
        self.rubber_action_button.setEnabled(True)
        self.restart_instruments()
   
    # Фунцкия возвращения изображения к исходному
    def startImagefunction(self):
        if self.flag_open_file:
            self.image = QImage(self.open_adres).scaled(QSize(self.monitor.width, self.monitor.height))   
            self.update()

    # Функция создания палитры цветов
    def add_palette_buttons(self, layout):
        for c in COLORS:
            b = QPaletteButton(c)
            b.pressed.connect(lambda c=c: self.setColor(c))
            layout.addWidget(b)

    # Функции undo/redo
    def can_undo_changed(self, enabled):
        self.actionUndo.setEnabled(enabled)

    def can_redo_changed(self, enabled):
        self.actionRedo.setEnabled(enabled)

    def make_undo_command(self):
        self.mUndoStack.push(UndoCommand(self))

    # Функция смены цвета кисти с помощью палитры
    def setColor(self, color):
        self.myPenColor = QColor(color)

    # Функция смены цвета кисти
    def setPenColor(self):
        self.myPenColor = self.shoose_color()
        # Сохранение предыдущего изображения
        self.image = self.image
        self.update()

    # Функция смены размера кисти
    def setPenSize(self):
        self.myPenWidth = self.brush_size_shoose.value()

    # Функции рисующих инструментов
    # Функция рисования кривой линии
    def draw(self, parent):
        self.painter = QPainter(parent)
        if self.drawingPath:
            self.painter.setPen(QPen(self.myPenColor,
                        self.myPenWidth, 
                        Qt.SolidLine, 
                        Qt.RoundCap,
                        Qt.RoundJoin))
            self.painter.begin(self.image)
            self.painter.drawPath(self.drawingPath)
            self.painter.end()
            
    #FIXME: исправить рисование прямой: когда рисуешь новую изначальная точка зависает 
    # на конечной точке последней отрисованной линии
    
    # Ластик
    def rubber(self, parent):
        painter = QPainter(parent)
        if self.rubberPath:
            painter.setPen(QPen(self.bg_color,
                        30, 
                        Qt.SolidLine, 
                        Qt.RoundCap,
                        Qt.RoundJoin))
            painter.drawPath(self.rubberPath)
            self.update()
            
    # Рисование прямой линии
    def draw_solid(self, parent):
        painter = QPainter(parent)
        if self.solidPath:
            painter.setPen(QPen(self.myPenColor,
                            self.myPenWidth, 
                            Qt.SolidLine, 
                            Qt.RoundCap,
                            Qt.RoundJoin))
            line = QLineF(self.last_position_solid, self.current_position_solid)
            painter.drawLine(line.p1(), line.p2())
            self.update()
            self.startPoint = self.endPoint = None
    
    # Рисование заполненного круга
    def draw_circle(self, parent):
        painter = QPainter(parent)
        if self.circlePath:
            painter.setBrush(QBrush(self.myPenColor))
            painter.setPen(self.myPenColor)
            radius = int(((self.sx - self.x1) ** 2 + (self.sy - self.y1) ** 2) ** 0.5)
            painter.drawEllipse(self.sx - radius, self.sy - radius, radius * 2, radius * 2)
            self.update()

    # Рисование пустого круга
    def draw_unfcircle(self, parent):
        painter = QPainter(parent)
        if self.circleunfPath:
            painter.setPen(QPen(self.myPenColor, self.myPenWidth))
            radius = int(((self.sx - self.x1) ** 2 + (self.sy - self.y1) ** 2) ** 0.5)
            painter.drawEllipse(self.sx - radius, self.sy - radius, radius * 2, radius * 2)
            self.update()

    # Рисование граффити
    def draw_sprey(self, parent):
        painter = QPainter(parent)
        if self.graffitiPath:
            painter.setPen(QPen(self.myPenColor, self.myPenWidth))
            # for _ in range(self.SPRAY_PARTICLES):
            for _ in range(500):
                xo = random.gauss(0, self.SPRAY_DIAMETER)
                yo = random.gauss(0, self.SPRAY_DIAMETER)
                painter.drawPoint(int(self.start_x + xo), int(self.start_y + yo))
            self.update()

    # Рисование заполненного прямоугольника
    def draw_rectangle(self, parent):
        painter = QPainter(parent)
        if self.rectanglePath:
            painter.setBrush(QBrush(self.myPenColor))
            painter.setPen(self.myPenColor)
            painter.drawRect(self.sx, self.sy, self.x1 - self.sx, self.y1 - self.sy)
            self.update()

    # Рисование пустого прямоугольника
    def draw_unfrectangle(self, parent):
        painter = QPainter(parent)
        if self.rectangleunfPath:
            painter.setPen(QPen(self.myPenColor, self.myPenWidth))
            painter.drawRect(self.sx, self.sy, self.x1 - self.sx, self.y1 - self.sy)
            self.update()

    # Рисование заполненного овала
    def draw_oval(self, parent):
        painter = QPainter(parent)
        if self.ovalPath:
            painter.setBrush(QBrush(self.myPenColor))
            painter.setPen(self.myPenColor)
            painter.drawRoundedRect(self.sx, self.sy, self.x1 - self.sx, self.y1 - self.sy, 360.0, 360.0)
            self.update()

    # Рисование пустого овала
    def draw_unfoval(self, parent):
        painter = QPainter(parent)
        if self.ovalunfPath:
            painter.setPen(QPen(self.myPenColor, self.myPenWidth))
            painter.drawRoundedRect(self.sx, self.sy, self.x1 - self.sx, self.y1 - self.sy, 360.0, 360.0)
            self.update()

    # Рисование полуокружности
    def draw_hord(self, parent):
        painter = QPainter(parent)
        if self.hordPath:
            painter.setBrush(QBrush(self.myPenColor))
            painter.setPen(QPen(self.myPenColor))
            painter.drawChord(self.sx, self.sy, (self.x1 - self.sx), int((self.y1 - self.sy) * 4), 30 * 16, 120 * 16)
            self.update()

    # Рисование дуги
    def draw_arc(self, parent):
        painter = QPainter(parent)
        if self.arcPath:
            painter.setBrush(QBrush(self.myPenColor))
            painter.setPen(QPen(self.myPenColor, self.myPenWidth))
            painter.drawArc(self.sx, self.sy, self.x1 - self.sx, (self.y1 - self.sy) * 4, 30 * 16, 120 * 16)

    # Функция отрисовывания при нажатой левой кнопке мыши
    def mousePressEvent(self, event):
        self.is_pressed = True
        if event.button() == Qt.LeftButton and self.drawing_curved_line:
            self.drawingPath = QPainterPath()
            self.drawingPath.moveTo(event.pos())
            self.update()
            self.make_undo_command()
        elif event.button() == Qt.LeftButton and self.drawing_rubber:
            self.rubberPath = QPainterPath()
            self.rubberPath.moveTo(event.pos())
            self.update()
            self.make_undo_command()
        elif event.button() == Qt.LeftButton and self.drawing_solid_line:
            self.solidPath = QPainterPath()
            self.last_position_solid = event.pos()
            self.update()
            self.make_undo_command()
        elif event.button() == Qt.LeftButton and self.drawing_graffiti:
            self.graffitiPath = QPainterPath()
            self.graffitiPath.moveTo(event.pos())
            self.update()
            self.make_undo_command()
        elif event.button() == Qt.LeftButton and self.drawing_circle:
            self.circlePath = QPainterPath()
            self.sx, self.sy, self.x1, self.y1 = event.x(), event.y(), event.x(), event.y()
            self.update()
            self.make_undo_command()
        elif event.button() == Qt.LeftButton and self.drawing_unfcircle:
            self.circleunfPath = QPainterPath()
            self.sx, self.sy, self.x1, self.y1 = event.x(), event.y(), event.x(), event.y()
            self.update()
            self.make_undo_command()
        elif event.button() == Qt.LeftButton and self.drawing_rectangle:
            self.rectanglePath = QPainterPath()
            self.sx, self.sy, self.x1, self.y1 = event.x(), event.y(), event.x(), event.y()
            self.update()
            self.make_undo_command()
        elif event.button() == Qt.LeftButton and self.drawing_unfrectangle:
            self.rectangleunfPath = QPainterPath()
            self.sx, self.sy, self.x1, self.y1 = event.x(), event.y(), event.x(), event.y()
            self.update()
            self.make_undo_command()
        elif event.button() == Qt.LeftButton and self.drawing_oval:
            self.ovalPath = QPainterPath()
            self.sx, self.sy, self.x1, self.y1 = event.x(), event.y(), event.x(), event.y()
            self.update()
            self.make_undo_command()
        elif event.button() == Qt.LeftButton and self.drawing_unfoval:
            self.ovalunfPath = QPainterPath()
            self.sx, self.sy, self.x1, self.y1 = event.x(), event.y(), event.x(), event.y()
            self.update()
            self.make_undo_command()
        elif event.button() == Qt.LeftButton and self.drawing_hord:
            self.hordPath = QPainterPath()
            self.sx, self.sy, self.x1, self.y1 = event.x(), event.y(), event.x(), event.y()
            self.update()
            self.make_undo_command()
        elif event.button() == Qt.LeftButton and self.drawing_arc:
            self.arcPath = QPainterPath()
            self.sx, self.sy, self.x1, self.y1 = event.x(), event.y(), event.x(), event.y()
            self.update()
            self.make_undo_command()
    
    # Функция рисования по мере движения мышью
    def mouseMoveEvent(self, event):
        if event.buttons() and Qt.LeftButton and self.drawingPath and self.drawing_curved_line:     
            self.drawingPath.lineTo(event.pos())
            self.update()
        elif event.buttons() and Qt.LeftButton and self.rubberPath and self.drawing_rubber:     
            self.rubberPath.lineTo(event.pos())
            self.update()
        elif event.buttons() and Qt.LeftButton and self.solidPath and self.drawing_solid_line: 
            if self.last_position_solid:
                self.solidPath.lineTo(event.pos())
                self.current_position_solid = event.pos()
                self.update()
        elif event.buttons() and Qt.LeftButton and self.graffitiPath and self.drawing_graffiti:
            self.start_x = event.x()
            self.start_y = event.y()
            self.draw_sprey(self.image)
            self.update()
        elif event.buttons() and Qt.LeftButton and self.circlePath and self.drawing_circle: 
            self.x1 = event.x()
            self.y1 = event.y()
            self.update()
        elif event.buttons() and Qt.LeftButton and self.circleunfPath and self.drawing_unfcircle: 
            self.x1 = event.x()
            self.y1 = event.y()
            self.update()
        elif event.buttons() and Qt.LeftButton and self.rectanglePath and self.drawing_rectangle: 
            self.x1 = event.x()
            self.y1 = event.y()
            self.update()
        elif event.buttons() and Qt.LeftButton and self.rectangleunfPath and self.drawing_unfrectangle: 
            self.x1 = event.x()
            self.y1 = event.y()
            self.update()
        elif event.buttons() and Qt.LeftButton and self.ovalPath and self.drawing_oval: 
            self.x1 = event.x()
            self.y1 = event.y()
            self.update()
        elif event.buttons() and Qt.LeftButton and self.ovalunfPath and self.drawing_unfoval: 
            self.x1 = event.x()
            self.y1 = event.y()
            self.update()
        elif event.buttons() and Qt.LeftButton and self.hordPath and self.drawing_hord: 
            self.x1 = event.x()
            self.y1 = event.y()
            self.update()
        elif event.buttons() and Qt.LeftButton and self.arcPath and self.drawing_arc: 
            self.x1 = event.x()
            self.y1 = event.y()
            self.update()

    # Функция прерывания рисования
    def mouseReleaseEvent(self, event):
        self.is_pressed = False
        if self.drawing_curved_line:
            self.make_undo_command()
            self.draw(self.image)
            self.update()
        elif self.drawing_rubber:
            self.make_undo_command()
            self.rubber(self.image)
            self.update()
        elif self.drawing_graffiti:
            self.make_undo_command()
        elif self.drawing_solid_line:
            if self.current_position_solid and self.last_position_solid:
                self.make_undo_command()
                self.draw_solid(self.image)
                self.update()
        elif self.drawing_circle:
            self.make_undo_command()
            self.draw_circle(self.image)
        elif self.drawing_unfcircle:
            self.make_undo_command()
            self.draw_unfcircle(self.image)
        elif self.drawing_rectangle:
            self.make_undo_command()
            self.draw_rectangle(self.image)
        elif self.drawing_unfrectangle:
            self.make_undo_command()
            self.draw_unfrectangle(self.image)
        elif self.drawing_oval:
            self.make_undo_command()
            self.draw_oval(self.image)
        elif self.drawing_unfoval:
            self.make_undo_command()
            self.draw_unfoval(self.image)
        elif self.drawing_hord:
            self.make_undo_command()
            self.draw_hord(self.image)
        elif self.drawing_arc:
            self.make_undo_command()
            self.draw_arc(self.image)

    # Функция действия рисования
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawImage(event.rect(), self.image, self.rect())
        # рисование кривой линии
        if self.is_pressed and self.drawing_curved_line:
            self.draw(self)
        # Ластик
        elif self.is_pressed and self.drawing_rubber:
            self.rubber(self)
        # Граффити
        elif self.is_pressed and self.drawing_graffiti:
            self.draw_sprey(self) 
        # Рисования прямой линии
        elif self.is_pressed and self.drawing_solid_line:
            if self.last_position_solid and self.current_position_solid:
                self.draw_solid(self)
        # Рисования круга
        elif self.is_pressed and self.drawing_circle:
            self.draw_circle(self)
        # Рисования пустого круга 
        elif self.is_pressed and self.drawing_unfcircle:
            self.draw_unfcircle(self)
        # Рисования заполненного прямоугольника
        elif self.is_pressed and self.drawing_rectangle:
            self.draw_rectangle(self)
        # Рисования пустого прямоугольника
        elif self.is_pressed and self.drawing_unfrectangle:
            self.draw_unfrectangle(self)
        # Рисования заполненного овала
        elif self.is_pressed and self.drawing_oval:
            self.draw_oval(self)
        # Рисования пустого овала
        elif self.is_pressed and self.drawing_unfoval:
            self.draw_unfoval(self)
        # Рисования полуокружности
        elif self.is_pressed and self.drawing_hord:
            self.draw_hord(self)
        # Рисования дуги
        elif self.is_pressed and self.drawing_arc:
            self.draw_arc(self)

    # Функция для проверки событий на комбинацию клавиш для выполнений команд redo/undo 
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Z and event.modifiers() == Qt.ControlModifier:  
            self.mUndoStack.undo()
        elif event.key() == Qt.Key_Y and event.modifiers() == Qt.ControlModifier:  
            self.mUndoStack.redo()
    
    # Функция выбора цвета 
    def shoose_color(self): 
        self.color = QColorDialog(self).getColor()
        return self.color
    
    #FIXME: При прерывании окна выбора цвета задний фон становится черным

    # Функция заливки холста
    def zalivka_function(self):
        self.bg_color = self.shoose_color()
        if self.bg_color:
            self.image.fill(self.bg_color)
     
    # Фунция сохранения изменений фотографии 
    def save_changed_function(self, changed_image): 
        self.copia = changed_image

    # Функция обнуления состояния рисования инструментов и снятия нажатия на их кнопки
    def restart_instruments(self):
        # Отключаем все инструменты рисования
        self.drawing_curved_line = False
        self.drawing_solid_line = False
        self.drawing_circle = False
        self.drawing_graffiti = False
        self.drawing_rubber = False
        self.drawing_unfcircle = False
        self.drawing_rectangle = False
        self.drawing_unfrectangle = False
        self.drawing_oval = False
        self.drawing_unfoval = False
        self.drawing_hord = False
        self.drawing_arc = False
        # Отключаем все активированные кнопки
        for button in self.list_instruments_buttons:
            button.setChecked(False)

    # Функция кисти в toolbar'е
    def activate_brush_function(self):
        if self.brush_button.isChecked():
            self.brush_on_function()
        else:
            self.brush_off_function()

    # Функция включения рисования кистью
    def brush_on_function(self):
        self.restart_instruments()
        self.drawing_curved_line = True
        self.brush_button.setChecked(True)

    # Функция отключения рисования кистью
    def brush_off_function(self):
        self.drawing_curved_line = False
        self.brush_button.setChecked(False)

    # Функция прямой линии
    def activate_solid_function(self):
        if self.solid_line_button.isChecked():
            self.solid_on_function()
        else:
            self.solid_off_function()
    
    # Функция включения рисования прямой
    def solid_on_function(self):
        self.restart_instruments()
        self.drawing_solid_line = True
        self.solid_line_button.setChecked(True)

    # Функция выключения рисования прямой
    def solid_off_function(self):
        self.drawing_solid_line = False
        self.solid_line_button.setChecked(False)

    # Функция активации рисования граффити
    def activate_graffiti_function(self):
        if self.graffiti_button.isChecked():
            self.graffiti_on_function()
        else:
            self.graffiti_off_function()

    # Функция включения рисования граффити
    def graffiti_on_function(self):
        self.restart_instruments()
        self.drawing_graffiti = True
        self.graffiti_button.setChecked(True)
    
    # Функция выключения рисования граффити
    def graffiti_off_function(self):
        self.drawing_graffiti = False
        self.graffiti_button.setChecked(False)

    # Функция активации рисования круга
    def activate_circle_function(self):
        if self.circle_button.isChecked():
            self.circle_on_function()
        else:
            self.circle_off_function()

    # Функция включения рисования круга
    def circle_on_function(self):
        self.restart_instruments()
        self.drawing_circle = True
        self.circle_button.setChecked(True)
    
    # Функция выключения рисования круга
    def circle_off_function(self):
        self.drawing_circle = False
        self.circle_button.setChecked(False)

    # Функции для проверки включения/выключения ластика 
    def activate_rubber_function(self):
        if self.rubber_action_button.isChecked():
            self.rubber_on_function()
        else:
            self.rubber_off_function()

    # Функция включения ластика
    def rubber_on_function(self):
        self.restart_instruments()
        self.drawing_rubber = True
        self.rubber_action_button.setChecked(True)
    
    # Функция выключения ластика
    def rubber_off_function(self):
        self.drawing_rubber = False
        self.rubber_action_button.setChecked(False)

    # Функция проверки включения/выключения незаполненного круга
    def activate_unf_circle_function(self):
        if self.unfilled_circle_button.isChecked():
            self.unf_circle_on_function()
        else:
            self.unf_circle_off_function()

    # Функция включения незаполненного круга
    def unf_circle_on_function(self):
        self.restart_instruments()
        self.drawing_unfcircle = True
        self.unfilled_circle_button.setChecked(True)
    
    # Функция выключения незаполненного круга
    def unf_circle_off_function(self):
        self.drawing_unfcircle = False
        self.unfilled_circle_button.setChecked(False)

    # Функция проверки включения/выключения прямоугольника
    def activate_rectangle_function(self):
        if self.filled_rectangle_button.isChecked():
            self.rectangle_on_function()
        else:
            self.rectangle_off_function()
    
    # Функция включения прямоугольника
    def rectangle_on_function(self):
        self.restart_instruments()
        self.drawing_rectangle = True
        self.filled_rectangle_button.setChecked(True)
    
    # Функция выключения прямоугольника
    def rectangle_off_function(self):
        self.drawing_rectangle = False
        self.filled_rectangle_button.setChecked(False)

    # Функция проверки включения/выключения незаполненного прямоугольника
    def activate_unfrectangle_function(self):
        if self.unfilled_rectangle_button.isChecked():
            self.unfrectangle_on_function()
        else:
            self.unfrectangle_off_function()
    
    # Функция включения незаполненного прямоугольника
    def unfrectangle_on_function(self):
        self.restart_instruments()
        self.drawing_unfrectangle = True
        self.unfilled_rectangle_button.setChecked(True)
    
    # Функция выключения незаполненного прямоугольника
    def unfrectangle_off_function(self):
        self.drawing_unfrectangle = False
        self.unfilled_rectangle_button.setChecked(False)

    # Функция проверки включения/выключения заполненного овала
    def activate_oval_function(self):
        if self.filled_oval_button.isChecked():
            self.oval_on_function()
        else:
            self.oval_off_function()
    
    # Функция включения овала
    def oval_on_function(self):
        self.restart_instruments()
        self.drawing_oval = True
        self.filled_oval_button.setChecked(True)

    # Функция выключения овала
    def oval_off_function(self):
        self.drawing_oval = False
        self.filled_oval_button.setChecked(False)
    
    # Функция проверки включения/выключения незаполненного овала
    def activate_unfoval_function(self):
        if self.unfilled_oval_button.isChecked():
            self.unfoval_on_function()
        else:
            self.unfoval_off_function()
    
    # Функция включения незаполненного овала
    def unfoval_on_function(self):
        self.restart_instruments()
        self.drawing_unfoval = True
        self.unfilled_oval_button.setChecked(True)

    # Функция выключения незаполненного овала
    def unfoval_off_function(self):
        self.drawing_unfoval = False
        self.unfilled_oval_button.setChecked(False)

    # Функция проверки включения/выключения полуокружности
    def activate_hord_function(self):
        if self.hord_button.isChecked():
            self.hord_on_function()
        else:
            self.hord_off_function()

    # Функция включения полуокружности
    def hord_on_function(self):
        self.restart_instruments()
        self.drawing_hord = True
        self.hord_button.setChecked(True)
    
    # Функция выключения полуокружности
    def hord_off_function(self):
        self.drawing_hord = False
        self.hord_button.setChecked(False)
    
    # Функция проверки включения/выключения дуги
    def activate_arc_function(self):
        if self.arc_button.isChecked():
            self.arc_on_function()
        else:
            self.arc_off_function()

    # Функция включения дуги
    def arc_on_function(self):
        self.restart_instruments()
        self.drawing_arc = True
        self.arc_button.setChecked(True)

    # Функция выключения дуги
    def arc_off_function(self):
        self.drawing_arc = False
        self.arc_button.setChecked(False)

    # Фильтры для изображений
    # Функция black изображения
    def black_filter(self):
        new_img = ImageQt.fromqimage(self.image)
        new_img = new_img.filter(ImageFilter.FIND_EDGES)
        new_img = new_img.convert("RGBA")
        data = new_img.tobytes("raw", "RGBA")
        self.image = QImage(data, new_img.size[0], 
                            new_img.size[1], 
                            QImage.Format_ARGB32)
        self.save_changed_function(self.image)
        self.update()
    
    # Функция white изображения
    def white_filter(self):
        new_img = ImageQt.fromqimage(self.image)
        new_img = new_img.filter(ImageFilter.CONTOUR)
        new_img = new_img.convert("RGBA")
        data = new_img.tobytes("raw", "RGBA")
        self.image = QImage(data, new_img.size[0], new_img.size[1], QImage.Format_ARGB32)
        self.save_changed_function(self.image)
        self.update()

    # Функция размытия изображения
    def blur_filter(self):
        new_img = ImageQt.fromqimage(self.image)
        new_img.filter(ImageFilter.BoxBlur(5))
        new_img = new_img.convert("RGBA")
        data = new_img.tobytes("raw", "RGBA")
        self.image = QImage(data, new_img.size[0], new_img.size[1], QImage.Format_ARGB32)
        self.save_changed_function(self.image)
        self.update()

    # Функция резкости изображения
    def detail_function(self):
        new_img = ImageQt.fromqimage(self.image)
        new_img = new_img.filter(ImageFilter.SHARPEN)
        new_img = new_img.convert("RGBA")
        data = new_img.tobytes("raw", "RGBA")
        self.image = QImage(data, new_img.size[0], new_img.size[1], QImage.Format_ARGB32)
        self.save_changed_function(self.image)
        self.update()

    # Функция основных моментов изображения
    def main_filter_function(self):
        new_img = ImageQt.fromqimage(self.image)
        new_img = new_img.filter(ImageFilter.DETAIL)
        new_img = new_img.convert("RGBA")
        data = new_img.tobytes("raw", "RGBA")
        self.image = QImage(data, new_img.size[0], new_img.size[1], QImage.Format_ARGB32)
        self.save_changed_function(self.image)
        self.update()
        
    # Функция добаления обьема в изображение
    def volume_function(self):
        new_img = ImageQt.fromqimage(self.image)
        new_img = new_img.filter(ImageFilter.EMBOSS)
        new_img = new_img.convert("RGBA")
        data = new_img.tobytes("raw", "RGBA")
        self.image = QImage(data, new_img.size[0], new_img.size[1], QImage.Format_ARGB32)
        self.save_changed_function(self.image)
        self.update()

    # Функция черно-белого фильтра изображения
    def black_white_function(self):
        new_img = ImageQt.fromqimage(self.image)
        new_img = ImageOps.grayscale(new_img)
        new_img = new_img.convert("RGBA")
        data = new_img.tobytes("raw", "RGBA")
        self.image = QImage(data, new_img.size[0], new_img.size[1], QImage.Format_ARGB32)
        self.save_changed_function(self.image)
        self.update()

    # Функция поворота изображения влево
    def image_rotate_left(self):
        self.degree -= 90
        self.degree %= 360
        t = QTransform().rotate(-90)
        self.image = self.image.transformed(t)
        if abs(self.degree) == 180 or abs(self.degree) == 0:
            new_height = self.monitor.height
            new_width = self.monitor.width
            self.image = self.image.scaled(QSize(new_width, new_height))
        else:
            new_height = (self.monitor.height ** 2) // self.monitor.width
            new_width = self.monitor.height
            self.image = self.image.scaled(QSize(new_height, new_width))
        self.update()

    # Функция поворота изображения вправо
    def image_rotate_right(self):
        self.degree += 90
        self.degree %= 360
        t = QTransform().rotate(90)
        self.image = self.image.transformed(t)
        if abs(self.degree) == 180 or abs(self.degree) == 0:
            new_height = self.monitor.height
            new_width = self.monitor.width
            self.image = self.image.scaled(QSize(new_width, new_height))
        else:
            new_height = (self.monitor.height ** 2) // self.monitor.width
            new_width = self.monitor.height
            self.image = self.image.scaled(QSize(new_height, new_width))
        self.update()

    # Функция зеркального изображения по горизонтали
    def image_mirror_horizontal(self):
        self.image = self.image.mirrored(True, False)
        self.update()

    # Функция зеркального изображения по вертикали
    def image_mirror_vertical(self):
        self.image = self.image.mirrored(False, True)
        self.update()

    # Функция появления окна для проверки сохранено ли изображение
    def closeEvent(self, event):
        # Если при выходе из нашего приложения наш рисунок не сохранен то:
        if not self.save_image_flag:
            # создаем обьект класса выводимого сообщения
            reply = QMessageBox.question(
                        self, 
                        "Вы точно хотите выйти?", 
                        "Сохранить изменениня?", 
                        QMessageBox.Yes | QMessageBox.No
            )
            # Если мы выбираем Yes то открывается меню сохранения файла
            if reply == QMessageBox.Yes:
                self.save_as_file_function()
            # Если мы выбираем No то наше приложение закрывается
            elif reply == QMessageBox.No:
                event.accept()
            else:
                return


# Запускаем наше приложение
if __name__ == "__main__":
    app = QApplication(sys.argv)
    photoshop = Photoshop()
    photoshop.show()
    sys.exit(app.exec())