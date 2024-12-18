#-----------------------------------------------------------------------------#
# Compact Brush Toggler - Copyright (c) 2021 - kaichi1342                     #
# ----------------------------------------------------------------------------#
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
# ----------------------------------------------------------------------------#
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.                        #
# See the GNU General Public License for more details.                        #
#-----------------------------------------------------------------------------#
# You should have received a copy of the GNU General Public License           #
# along with this program.                                                    #
# If not, see https://www.gnu.org/licenses/                                   #
# ----------------------------------------------------------------------------#
# Thank you to: AkiR , Grum999, KnowZero                                      #
# Who provided much of the base code and helped me making this.               #
# -----------------------------------------------------------------------------
# This is docker that  toggle pen pressure on/off of 6 brush property         #
# [Size, Opacity, Flow, Softness, Scatter, Rotation ] and adjust              #
# brush hfade without opening the Brush Editor.                               #
# -----------------------------------------------------------------------------
  
from krita import DockWidget, DockWidgetFactory, DockWidgetFactoryBase

import krita, time, os
 
from PyQt5.QtCore import (
    QSize, QTimer, Qt, pyqtSignal
)
from PyQt5.QtGui import (
    QPalette
)
from PyQt5.QtWidgets import (
    QApplication,
    QWidget, QLabel, QSlider,
    QVBoxLayout,  QHBoxLayout,  QGridLayout,  
    QPushButton,QDoubleSpinBox,  
    QToolButton, QSizePolicy
        
)


from .CBT_Icons import * 
from .CBT_Toggler import * 


DOCKER_NAME = 'CompactBrushToggler'
DOCKER_ID = 'pykrita_compactbrushtoggler'


class CBTDoubleSpinBox(QDoubleSpinBox):
    stepChanged = pyqtSignal() 

    def stepBy(self, step):
        value = self.value()
        super(CBTDoubleSpinBox, self).stepBy(step)
        if self.value() != value:
            self.stepChanged.emit()

    def focusOutEvent(self, e):
        value = self.value() 
        super(CBTDoubleSpinBox, self).focusOutEvent(e)
        self.stepChanged.emit()


class CompactBrushToggler(DockWidget):
    
    theme_color = {
        "dark"  : {"on" :  "background-color : #305475; color : #D2D2D2;", "off" : "background-color : #383838 ; color : #D2D2D2;", "disabled" : "background-color : #1a1a1a; color : #9A9A9A;"},
        "light" : {"on" :  "background-color : #8BD5F0; color : #9A9A9A;", "off" : "background-color : #1a1a1a ; color : #373737;", "disabled" : "background-color : #9A9A9A; color : #2a2a2a;"}
    } 
    

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Compact Brush Toggler") 
        instance.notifier().windowCreated.connect(self.createActions)

        self.baseWidget = QWidget()
         
        self.vbox = QVBoxLayout()
        self.vbox.setContentsMargins(2, 2, 2, 2)

        self.baseWidget.setLayout(self.vbox)
        self.setWidget(self.baseWidget)
        
        self.createdActions = False
        
        self.theme      = "dark"
        self.theme_signal  = False 

        self.toggler    = CBT_Toggler(self, self.theme_color) 
        self.toggler.setTheme(self.theme)
        
        for prop in self.toggler.property.keys():
            self.toggler.property[prop].value = True; 
    
        self.setUI_H() 

    # UI LAYOUT
    def setUI_H(self):

        self.baseWidget.setMinimumSize(QSize(60,100))
        self.baseWidget.setMaximumSize(QSize(450,850)) 

        self.timer = QTimer() 

        self.hRow1 = QWidget()
        self.toolGrid1 = QGridLayout()
        self.toolGrid1.setContentsMargins(1, 1, 1, 0) 
        self.hRow1.setLayout(self.toolGrid1)
          
        self.hRow2 = QWidget()
        self.toolGrid2 = QGridLayout()
        self.toolGrid2.setContentsMargins(1, 1, 1, 2)  
        self.hRow2.setLayout(self.toolGrid2)

        self.hRow3 = QWidget()
        self.toolGrid3 = QHBoxLayout()
        self.toolGrid3.setContentsMargins(1, 1, 1, 2) 
        self.toolGrid3.setAlignment(Qt.AlignRight)
        self.hRow3.setLayout(self.toolGrid3)

        self.lbl_BrushFade       = QLabel("Softness")
        self.BrushFadeSlider     = QSlider(Qt.Horizontal)
        self.BrushFade           = CBTDoubleSpinBox()

        self.lbl_Toggle       = QLabel("Toggles")
  
        self.vbox.addWidget(self.hRow1)    
        self.vbox.addWidget(self.hRow2)    

        self.BrushProperty       = { }

        i = 0 
        for prop in self.toggler.property.keys(): 
            self.BrushProperty[prop] =  QPushButton() 
            self.BrushProperty[prop].setToolTip("Toggle Brush " + self.toggler.translation[prop]["tr"] )
            self.BrushProperty[prop].setSizePolicy( QSizePolicy.Preferred, QSizePolicy.Expanding )
            self.toolGrid2.addWidget(self.BrushProperty[prop], i // 2, i % 2) 
            i += 1
    

        self.BrushFade.setRange(0, 1.0)
        self.BrushFade.setSingleStep(.01) 

        self.BrushFadeSlider.setRange(0,100)  
        self.BrushFadeSlider.setTickPosition(QSlider.NoTicks)
        self.BrushFadeSlider.setTickInterval(1)
  
       
        #self.toolGrid1.addWidget(self.lbl_BrushFade, 0, 0)
        self.toolGrid1.addWidget(self.BrushFadeSlider, 0, 0, 0, 5)
        self.toolGrid1.addWidget(self.BrushFade, 0, 6)


        self.brushPropertyConnect()
         
        self.BrushFadeSlider.valueChanged.connect(lambda:  self.sliderFadeChange()) 
        self.BrushFadeSlider.sliderReleased.connect(lambda:  self.changeFadeValue()) 
        self.BrushFade.stepChanged.connect(lambda:  self.spinnerChangedFadeValue()) 

        self.toggler.setInputItems(self.BrushProperty, self.BrushFade, self.BrushFadeSlider)

        for prop in self.toggler.property.keys(): 
            self.toggler.toggleIcon(prop)

        self.timer.timeout.connect(self.toggler.loadBrushInfo)

    #----------------------------------------------------#
    # Events and Connection                              #
    #                                                    #
    #----------------------------------------------------#
        
    def resizeEvent(self, event):    
        self.setNames()
    
    def canvasChanged(self, canvas):    
        if canvas:       
            if canvas.view():
                self.timer.start(300)  
                
                if self.theme_signal == False:
                    self.Window_Connect()
                
        else:
            self.timer.stop() 

    def brushPropertyConnect(self):
        self.BrushProperty["Size"].clicked.connect(lambda: self.toggler.toggleOptions("Size"))
        self.BrushProperty["Opacity"].clicked.connect(lambda: self.toggler.toggleOptions("Opacity"))
        self.BrushProperty["Flow"].clicked.connect(lambda: self.toggler.toggleOptions("Flow"))
        self.BrushProperty["Softness"].clicked.connect(lambda: self.toggler.toggleOptions("Softness"))
        self.BrushProperty["Rotation"].clicked.connect(lambda: self.toggler.toggleOptions("Rotation"))
        self.BrushProperty["Scatter"].clicked.connect(lambda: self.toggler.toggleOptions("Scatter"))
        self.BrushProperty["Color Rate"].clicked.connect(lambda: self.toggler.toggleOptions("Color Rate"))
        self.BrushProperty["Overlay Mode"].clicked.connect(lambda: self.toggler.toggleOptions("Overlay Mode"))
        self.BrushProperty["Ink depletion"].clicked.connect(lambda: self.toggler.toggleOptions("Ink depletion"))
        self.BrushProperty["Painting Mode"].clicked.connect(lambda: self.toggler.toggleOptions("Painting Mode")) 
    
    def showEvent(self, event):
        # Window 
        self.setNames()
        self.Theme_Changed()  
        self.Window_Connect()


    def Window_Connect(self):
        # Window
        self.window = Krita.instance().activeWindow() 
        
        if self.window != None:  
            self.window.themeChanged.connect(self.Theme_Changed)  
            self.theme_signal = True
            

    def Theme_Changed(self):
        theme = QApplication.palette().color(QPalette.Window).value()
        
        if theme > 128: 
            self.theme  = "light"
            self.toggler.setTheme(self.theme)
            self.toggler.cbt_icons.setTheme("dark")   
        else: 
            self.theme  = "dark"
            self.toggler.setTheme(self.theme)
            self.toggler.cbt_icons.setTheme("light") 

        for prop in self.toggler.property.keys(): 
            self.toggler.toggleIcon(prop)

    def createActions(self):
        if not self.createdActions:
            self.createdActions = True
            window = instance.activeWindow()
            window.createAction('toggle_pressure_size').triggered.connect(lambda: self.toggler.toggleOptions("Size"))
            window.createAction('toggle_pressure_opacity').triggered.connect(lambda: self.toggler.toggleOptions("Opacity"))
            window.createAction('toggle_pressure_flow').triggered.connect(lambda: self.toggler.toggleOptions("Flow"))
            window.createAction('toggle_pressure_softness').triggered.connect(lambda: self.toggler.toggleOptions("Softness"))
            window.createAction('toggle_pressure_rotation').triggered.connect(lambda: self.toggler.toggleOptions("Rotation")) 
            window.createAction('toggle_pressure_scatter').triggered.connect(lambda: self.toggler.toggleOptions("Scatter"))
 
            window.createAction('toggle_pressure_colrate').triggered.connect(lambda: self.toggler.toggleOptions("Color Rate"))
            window.createAction('toggle_overlay').triggered.connect(lambda: self.toggler.toggleOptions("Overlay Mode"))

            window.createAction('toggle_soak').triggered.connect(lambda: self.toggler.toggleOptions("Ink depletion"))
            window.createAction('toggle_painting_mode').triggered.connect(lambda: self.toggler.toggleOptions("Painting Mode"))
        
    #----------------------------------------------------#
    # Connect Functions                                  #
    #                                                    #
    #----------------------------------------------------#
    def setNames(self):
        #self.Theme_Changed()
        ratio =  self.BrushProperty["Size"].width() / self.BrushProperty["Size"].height() 
       
        if ratio > 4:
            for prop in self.toggler.property.keys():   
                self.BrushProperty[prop].setText( self.toggler.translation[prop]["tr"]) 
        elif ratio > 2:
            for prop in self.toggler.property.keys():   
                self.BrushProperty[prop].setText( self.toggler.translation[prop]["abr"]) 
        else:  
            for prop in self.toggler.property.keys():  
                self.BrushProperty[prop].setText("")
        
        for prop in self.toggler.property.keys():  
            ico_size = QSize(
                int(self.BrushProperty[prop].height() - ( self.BrushProperty[prop].height() * .20)),
                int(self.BrushProperty[prop].width() - ( self.BrushProperty[prop].width() * .20)),
            )
             
            self.BrushProperty[prop].setIconSize( ico_size )

    def reloadPreset(self):
        #Krita.instance().action('reload_preset_action').trigger() 
        #self.toggler.loadState()
        pass
        
            
    def loadBrushState(self):   
        self.toggler.loadState()

    #----------------------------------------------------#
    # Toggle And Change Function                         #
    #                                                    #
    #----------------------------------------------------# 
    def sliderFadeChange(self):    
        self.BrushFade.setValue(self.BrushFadeSlider.value()/100)  
 
    def spinnerChangedFadeValue(self): 
        self.BrushFadeSlider.setValue(int(self.BrushFade.value()*100))
        self.changeFadeValue()
    
    def changeFadeValue(self): 
        self.toggler.cur_size  = Krita.instance().activeWindow().activeView().brushSize()    
        self.toggler.setBrushFadeValue()
        self.toggler.setBrushSize()
 
     

instance = Krita.instance()
dock_widget_factory = DockWidgetFactory(DOCKER_ID,
                                        DockWidgetFactoryBase.DockRight,
                                        CompactBrushToggler)

instance.addDockWidgetFactory(dock_widget_factory)