import numpy as np


def compute_transformation_matrix(livox_file, riegl_file, output_file):
    # Load 3D points from Livox and Riegl data files
    points_livox = np.loadtxt(livox_file, delimiter=',', usecols=[1, 2, 3])
    points_riegl = np.loadtxt(riegl_file, delimiter=',', usecols=[1, 2, 3])

    # Convert to homogeneous coordinates
    points_livox = np.r_[points_livox.T, np.ones((1, 4))]
    points_riegl = np.r_[points_riegl.T, np.ones((1, 4))]

    # Solve for the transformation matrix using least squares
    M, resid, rank, sing = np.linalg.lstsq(points_livox.T, points_riegl.T)

    # Transpose the matrix for correct orientation
    M = M.T

    # Save the transformation matrix to a file
    np.savetxt(output_file, M, fmt='%.15f')


# Example usage
# compute_transformation_matrix('../picking_list_livox.txt',
#                               '../picking_list_riegl.txt',
#                               'M_riegl_livox.txt')
