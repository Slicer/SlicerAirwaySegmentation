# Airway Segmentation

3D Slicer extension for airway segmentation in chest CT images.

The extension contains two modules:
- Airway Segmentation: This is a simple module that segments the airways from a CT image. The user needs to only specify the input volume and a markup point placed in the trachea. The module automatically retrieves the convolution kernel of the image if the image is loaded from DICOM (otherwise `STANDARD` kernel is used). The result is saved into a segmentation node. The module uses `Airway Segmentation CLI` module internally.
- Airway Segmentation CLI: CLI module that implements the segmentation algorithm. It uses a modified version of ITK's `itkConnectedThresholdImageFilter`' to segment all the pixels with an intensity below a threshold. The threshold is automatically identified by the module. The input seed point is used as starting point for the region growing segmentation. The user needs to specify the convolution kernel used for reconstructing the DICOM image.

The repository was forked from https://github.com/PietroNardelli/Slicer-AirwaySegmentation because the maintainer did not merge pull requests for several years.

![](Screenshot01.jpg)

## Tutorial

- Go to `Sample Data` module
- Click on `CTChest` to load the CT chest sample data set into the scene
- Go to `Markups` module
- Click `+ Point list` button to create a new point list
- Click in the trachea in any slice view
- Go to `Airway Segmentation` module
- Select `CTChest` as CT volume
- Select `F` as Seed point
- Click `Apply`

## User interface

- Inputs
  - `CT volume`: Input chest CT dataset to be segmented.
  - `Seed point`: Seed point for the algorithm. Only one seed point must be placed within the trachea. If using a pig CT chest image, the fiducial has to be placed between the carina and the further branch coming out of the trachea.
- Outputs
  - `Segmentation`: Output segmentation. If left at default then a new segmentation is created automatically.

## Related extensions

- [Lung CT analyzer](https://github.com/rbumm/SlicerLungCTAnalyzer#lung-ct-analyzer)

## References

Nardelli, P., Khan, K. A., Corvò, A., Moore, N., Murphy, M. J., Twomey, M.,  O'Connor, O. J., Kennedy, M. P., Estépar, R. S. J., Maher, M. M. & Cantillon-Murphy, P. (2015). Optimizing parameters of an open-source airway segmentation algorithm using different CT images. Biomedical engineering online, 14(1), 62.

## Acknowledgments

This work is supported by NA-MIC, the Slicer Community and University College of Cork.

- Author: [Pietro Nardelli](pie.nardelli@gmail.com) (University College Cork)
- Contributor: Andras Lasso (PerkLab, Queen's University)
