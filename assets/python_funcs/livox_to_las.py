import laspy
import numpy as np

def livox_corr_las(infile,outfile=None):
    import pointcloud_processing_functions as pcp
    '''
    Function to remove 0.0 coordinate entries in Livox point clouds. Currently considers XYZ only. Extend the function if attributes should be read and written as well (see further parameters of pcp functions).
    :param infile: 
    :param outfile: 
    :return: 
    '''

    data = pcp.read_las(infile)
    cloud = data[~np.all(data == 0.0, axis=1)]

    if outfile:
        pcp.write_las(cloud, outfile)
    return cloud

if __name__ == '__main__':

    import os

    # specify the data path
    data_path = 'Livox'

    # check if the specified path exists
    if not os.path.isdir(data_path):
        print(f'ERROR: {data_path} does not exist')
        print('Please specify the correct path to the data directory by replacing <path-to-data> above.')

    # sub-directory containing the point clouds
    pc_dir = os.path.join(data_path, '')

    # list of point clouds (time series)
    pc_list_all = os.listdir(pc_dir)

    pc_list = []
    for pc in pc_list_all:
        if (pc.endswith('las') or pc.endswith('laz')):
            print(f'Converting {pc}...')
            pc_path = f'{data_path}/{pc}'
            cloud = livox_corr_las(pc_path,outfile=pc_path.replace('.','_corr.'))