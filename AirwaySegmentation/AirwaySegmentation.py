import os
import unittest
import logging
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin


#
# AirwaySegmentation
#

class AirwaySegmentation(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Airway Segmentation"
    self.parent.categories = ["Segmentation"]
    self.parent.dependencies = []
    self.parent.contributors = ["Pietro Nardelli (University College Cork)"]
    self.parent.helpText = """
Segment airways on CT images from a single input point in the trachea.
"""
    self.parent.acknowledgementText = """
This file was originally developed by Pietro Nardelli, University College of Cork (UCC).
"""

#
# AirwaySegmentationWidget
#

class AirwaySegmentationWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent=None):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.__init__(self, parent)
    VTKObservationMixin.__init__(self)  # needed for parameter node observation
    self.logic = None
    self._parameterNode = None
    self._updatingGUIFromParameterNode = False

  def setup(self):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.setup(self)

    # Load widget from .ui file (created by Qt Designer).
    # Additional widgets can be instantiated manually and added to self.layout.
    uiWidget = slicer.util.loadUI(self.resourcePath('UI/AirwaySegmentation.ui'))
    self.layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)

    # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
    # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
    # "setMRMLScene(vtkMRMLScene*)" slot.
    uiWidget.setMRMLScene(slicer.mrmlScene)

    # Create logic class. Logic implements all computations that should be possible to run
    # in batch mode, without a graphical user interface.
    self.logic = AirwaySegmentationLogic()

    # #
    # # Link to Bronchoscopy Module
    # #
    # self.bronchoscopyButton = qt.QPushButton("Link To Bronchoscopy Navigation")
    # self.bronchoscopyButton.toolTip = "Connect to the Bronchoscopy module."
    # #self.bronchoscopyButton.checkable = True
    # self.bronchoscopyButton.enabled = False
    # self.bronchoscopyButton.setFixedSize(200,50)
    # self.layout.addWidget(self.bronchoscopyButton, 0, 4)
    # self.bronchoscopyButton.connect('clicked(bool)', self.onBronchoscopyButton)

    # Connections

    # These connections ensure that we update parameter node when scene is closed
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

    # These connections ensure that whenever user changes some settings on the GUI, that is saved in the MRML scene
    # (in the selected parameter node).
    self.ui.inputVolumeSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
    self.ui.inputSeedSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)

    # Buttons
    self.ui.applyButton.connect('clicked(bool)', self.onApplyButton)

    # Make sure parameter node is initialized (needed for module reload)
    self.initializeParameterNode()

  def cleanup(self):
    """
    Called when the application closes and the module widget is destroyed.
    """
    self.removeObservers()

  def enter(self):
    """
    Called each time the user opens this module.
    """
    # Make sure parameter node exists and observed
    self.initializeParameterNode()

  def exit(self):
    """
    Called each time the user opens a different module.
    """
    # Do not react to parameter node changes (GUI wlil be updated when the user enters into the module)
    self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

  def onSceneStartClose(self, caller, event):
    """
    Called just before the scene is closed.
    """
    # Parameter node will be reset, do not use it anymore
    self.setParameterNode(None)

  def onSceneEndClose(self, caller, event):
    """
    Called just after the scene is closed.
    """
    # If this module is shown while the scene is closed then recreate a new parameter node immediately
    if self.parent.isEntered:
      self.initializeParameterNode()

  def initializeParameterNode(self):
    """
    Ensure parameter node exists and observed.
    """
    # Parameter node stores all user choices in parameter values, node selections, etc.
    # so that when the scene is saved and reloaded, these settings are restored.

    self.setParameterNode(self.logic.getParameterNode())

    # Select default input nodes if nothing is selected yet to save a few clicks for the user
    if not self._parameterNode.GetNodeReference("InputVolume"):
      firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
      if firstVolumeNode:
        self._parameterNode.SetNodeReferenceID("InputVolume", firstVolumeNode.GetID())

    if not self._parameterNode.GetNodeReference("InputSeed"):
      firstPointsNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLMarkupsFiducialNode")
      if firstPointsNode:
        self._parameterNode.SetNodeReferenceID("InputSeed", firstPointsNode.GetID())


  def setParameterNode(self, inputParameterNode):
    """
    Set and observe parameter node.
    Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
    """

    if inputParameterNode:
      self.logic.setDefaultParameters(inputParameterNode)

    # Unobserve previously selected parameter node and add an observer to the newly selected.
    # Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
    # those are reflected immediately in the GUI.
    if self._parameterNode is not None:
      self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
    self._parameterNode = inputParameterNode
    if self._parameterNode is not None:
      self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

    # Initial GUI update
    self.updateGUIFromParameterNode()

  def updateGUIFromParameterNode(self, caller=None, event=None):
    """
    This method is called whenever parameter node is changed.
    The module GUI is updated to show the current state of the parameter node.
    """

    if self._parameterNode is None or self._updatingGUIFromParameterNode:
      return

    # Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause infinite loop)
    self._updatingGUIFromParameterNode = True

    # Update node selectors and sliders
    self.ui.inputVolumeSelector.setCurrentNode(self._parameterNode.GetNodeReference("InputVolume"))
    self.ui.inputSeedSelector.setCurrentNode(self._parameterNode.GetNodeReference("InputSeed"))
    self.ui.outputSegmentationSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputSegmentation"))

    # Update buttons states and tooltips
    if self._parameterNode.GetNodeReference("InputVolume") and self._parameterNode.GetNodeReference("InputSeed"):
      self.ui.applyButton.toolTip = "Compute airway segmentation"
      self.ui.applyButton.enabled = True
    else:
      self.ui.applyButton.toolTip = "Select input CT volume and seed point"
      self.ui.applyButton.enabled = False

    # All the GUI updates are done
    self._updatingGUIFromParameterNode = False

  def updateParameterNodeFromGUI(self, caller=None, event=None):
    """
    This method is called when the user makes any change in the GUI.
    The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
    """

    if self._parameterNode is None or self._updatingGUIFromParameterNode:
      return

    wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

    self._parameterNode.SetNodeReferenceID("InputVolume", self.ui.inputVolumeSelector.currentNodeID)
    self._parameterNode.SetNodeReferenceID("InputSeed", self.ui.inputSeedSelector.currentNodeID)
    self._parameterNode.SetNodeReferenceID("OutputVolume", self.ui.outputSegmentationSelector.currentNodeID)

    self._parameterNode.EndModify(wasModified)

  def onApplyButton(self):
    """
    Run processing when user clicks "Apply" button.
    """

    # Get convolution kernel
    inputVolume = self.ui.inputVolumeSelector.currentNode()
    convolutionKernel = self.logic.convolutionKernelFromVolumeNode(inputVolume)
    if not convolutionKernel:
      if not slicer.util.confirmOkCancelDisplay("Convolution kernel cannot be determined from the input volume."
        " The current input volume is not loaded from DICOM or the Convolution Kernel (0018,1210) field is missing."
        " Click OK to use STANDARD convolution kernel.",
        dontShowAgainSettingsKey = "AirwaySegmentation/DontShowDICOMImageExpectedWarning"):
        return False

    self.ui.applyButton.enabled = False
    slicer.app.processEvents()

    with slicer.util.tryWithErrorDisplay("Failed to compute results.", waitCursor=True):

      # Create output segmentation node, if not created yet
      segmentationNode = self.ui.outputSegmentationSelector.currentNode()
      if not segmentationNode:
        segmentationNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLSegmentationNode', slicer.mrmlScene.GetUniqueNameByString('Airway'))
        self.ui.outputSegmentationSelector.setCurrentNode(segmentationNode)

      # Compute output
      self.logic.process(inputVolume, self.ui.inputSeedSelector.currentNode(), segmentationNode)
      self.logic.show3D(segmentationNode)

    self.ui.applyButton.enabled = True

  # def onBronchoscopyButton(self):
  #   self.bronchoscopyButton.enabled = True
  #   mainWindow = slicer.util.mainWindow()
  #   mainWindow.moduleSelector().selectModule('Bronchoscopy')

#
# AirwaySegmentationLogic
#

class AirwaySegmentationLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self):
    """
    Called when the logic class is instantiated. Can be used for initializing member variables.
    """
    ScriptedLoadableModuleLogic.__init__(self)

  def setDefaultParameters(self, parameterNode):
    """
    Initialize parameter node with default settings.
    """
    pass

  def process(self, inputVolume, inputSeed, outputSegmentation):
    """
    Run the processing algorithm.
    Can be used without GUI widget.
    :param inputVolume: input CT volume to segment the airways from
    :param inputSeed: markup point node containint a single point in the trachea
    :param outputSegmentation: segmentation result
    """

    if not inputVolume or not inputSeed or not outputSegmentation:
      raise ValueError("Input volume or seed or output segmentation is invalid")

    import time
    startTime = time.time()
    logging.info('Processing started')


    # Get convolution kernel
    convolutionKernel = self.convolutionKernelFromVolumeNode(inputVolume)
    if not convolutionKernel:
      logging.warning("Convolution kernel is unknown, STANDARD will be used.")
      convolutionKernel = "STANDARD"

    # Compute the segmentation
    tmpLabelVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLabelMapVolumeNode")
    tmpLabelVolume.CreateDefaultDisplayNodes()
    tmpLabelVolume.GetDisplayNode().SetAndObserveColorNodeID('vtkMRMLColorTableNodeFileGenericAnatomyColors.txt')
    labelValue = 170  # trachea in GenericAnatomyColors
    parameters = {
        "inputVolume": inputVolume.GetID(),
        "reconstructionKernelType": convolutionKernel,
        "label": tmpLabelVolume.GetID(),
        "seed": inputSeed.GetID(),
        "labelValue": labelValue,
        }
    cliNode = slicer.cli.run(slicer.modules.airwaysegmentationcli, None, parameters, wait_for_completion = True)
    # We don't need the CLI module node anymore, remove it to not clutter the scene with it
    slicer.mrmlScene.RemoveNode(cliNode)

    # Convert result to segmentation node
    outputSegmentation.GetSegmentation().RemoveAllSegments()
    slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(tmpLabelVolume, outputSegmentation)
    # Use a lower smoothing than the default 0.5 to ensure that thin airways are not suppressed in the 3D output
    outputSegmentation.GetSegmentation().SetConversionParameter("Smoothing factor","0.2")

    segmentId = outputSegmentation.GetSegmentation().GetNthSegmentID(0)
    segment = outputSegmentation.GetSegmentation().GetSegment(segmentId)
    segment.SetTag(segment.GetTerminologyEntryTagName(),
      "Segmentation category and type - 3D Slicer General Anatomy list"
      "~SCT^123037004^Anatomical Structure"
      "~SCT^44567001^Trachea"
      "~^^"
      "~Anatomic codes - DICOM master list"
      "~^^"
      "~^^")

    slicer.mrmlScene.RemoveNode(tmpLabelVolume)

    stopTime = time.time()
    logging.info(f'Processing completed in {stopTime-startTime:.2f} seconds')

  def convolutionKernelFromVolumeNode(self, inputVolume):
    convolutionKernel = None
    instUIDs = inputVolume.GetAttribute('DICOM.instanceUIDs')
    if instUIDs:
      fileName = slicer.dicomDatabase.fileForInstance(instUIDs.split()[0])
      convolutionKernel = slicer.dicomDatabase.fileValue(fileName,'0018,1210')
    return convolutionKernel

  def show3D(self, segmentationNode):
    """
    Create and show airway in 3D
    """

    segmentationNode.CreateClosedSurfaceRepresentation()

    lm = slicer.app.layoutManager()
    threeDView = lm.threeDWidget( 0 ).threeDView()
    threeDView.resetFocalPoint()
    threeDView.lookFromViewAxis(ctk.ctkAxesWidget().Anterior)


#
# AirwaySegmentationTest
#

class AirwaySegmentationTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear()

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_AirwaySegmentation1()

  def test_AirwaySegmentation1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")

    # Get/create input data

    import SampleData
    inputVolumeNode = SampleData.downloadSample('CTChest')
    self.delayDisplay('Loaded test data set')

    inputSeedNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")
    inputSeedNode.AddControlPointWorld([-9.8, 3.4, -40.9])

    outputSegmentationNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")

    # Test the module logic

    logic = AirwaySegmentationLogic()

    self.delayDisplay('Compute the segmentation')
    logic.process(inputVolumeNode, inputSeedNode, outputSegmentationNode)
    logic.show3D(outputSegmentationNode)

    # Check if there is a segment in the output segmentation
    self.assertEqual(outputSegmentationNode.GetSegmentation().GetNumberOfSegments(), 1)

    # Check if the segment center is at the expected position.
    # Use a large absolute tolerance of 5.0mm as we just want to check if the segmentation was generally succeeded.
    expectedsegmentCenter = (-5.5, -5.9, -100.3)
    segmentId = outputSegmentationNode.GetSegmentation().GetNthSegmentID(0)
    segmentCenter = outputSegmentationNode.GetSegmentCenter(segmentId)
    import numpy as np
    self.assertTrue(np.allclose(segmentCenter, expectedsegmentCenter, atol=5.0))

    self.delayDisplay('Test passed')
