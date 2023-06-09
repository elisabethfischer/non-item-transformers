Format of the Index File
=============================
The goal of using index files in this project is to provide direct access to sessions in csv files.
There are two kinds generated by the framework - Session Index Files and Next Item Position Files (NIP).


Session Index File
------------------
Each sequence in a csv file consists of consecutive lines. 
Session Index Files are used to easily access such a sequence. 
They are binary and contain the start and end offset of each sequence and the total number of sequences of the respective csv file.
In so doing, all values are encoded in unsigned int64. 
  
The structure looks like the following::

  <start_offset_1><end_offset_1><start_offset_2><end_offset_2>...<num_seq>


Next Item Position File
-----------------------
The NIP file consists of a list of tuples containing the sequence id and a position in that sequence.
Therefore, truncating the sequences is a possible usage.
The end of the file holds the number of tuples.
Again, all values are encoded in unsigned int64.

The structure looks like the following::

  <seq_id><seq_position>...<num_tuples>


The index file can be used in the following scenarios:

  - You want to train your model on/ evaluate your model for all positions in the sequence: 
    
    - For example, consider the sequence [1, 2, 3, 4, 5] with id 42. 
      The file could contain the following information:

      (42, 1), (42, 2), (42, 3) (note: positions start at 0) 

      The corresponding dataset can then use the indices to return the following sequences:

      [1], [1, 2], [1, 2, 3], [1, 2, 3, 4] (maybe with targets 2, 3, 4, 5 respectively)

  - Leave-one-out-evaluation/training:
    
    - One single sequence datafile can be used for training, validation, and test
      using different sequence position indices.