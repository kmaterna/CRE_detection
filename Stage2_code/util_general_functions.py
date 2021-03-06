"""
Here we have some useful functions for reading sac files and input files 
That are common to most scripts to analyze CRE familes. 

"""

from obspy.core.stream import Stream
from obspy import read
import numpy as np 



def get_dirs_for_station(station_location_file):
	# Read the station location file, generate the directories where the sac files live.
	stations=[]; station_paths=[];
	ifile=open(station_location_file);
	for line in ifile:
		temp=line.split();
		# u=temp[0].decode("utf-8-sig");
		# s=u.encode("utf-8");  # issues with the first line of the text file and its utf-8 encoding. 
		s=temp[0];
		stations.append(s)
		station_paths.append(temp[3]);
	ifile.close();
	return [stations, station_paths];



def get_info_from_sac(filename):
	# Use Obspy Read to gather the location metadata for a particular SAC file. 
	st1 = read(filename);
	tr1 = st1[0]
	temp1=tr1.stats;
	d1 = temp1['sac']
	latitude1=float(d1['evla'])
	longitude1=float(d1['evlo'])
	depth=float(d1['evdp'])
	magnitude=float(d1['mag'])
	loc_type=str(d1['kuser0']).lower();
	return [longitude1, latitude1, depth, magnitude, loc_type];


def get_float_time_from_name(name):
	# Converts something like "2012.121.034422.71773265.sac" into a floating point decimal year (2010.26928) . 
	decyear=float(name[0:4])+float(name[5:8])/365.24+float(name[9:11])/(24*365.24)+float(name[11:13])/(24*60*365.24)+float(name[13:15])/(24*60*60*365.24);
	return decyear;



def read_family_line(line):
	# This is a very general function that reads a line from the family summary file
	# n*(time) n*(lon) n*(lat) n*(depth) n*(mag) best_station n*(loc_type) slip_rate
	
	time=[]; name=[]; lat=[]; lon=[]; mag=[]; depth=[]; type_of_loc=[]; # input arrays for each family. 

	# Go read in the timing and location information for each family from the files
	temp1=line.split();
	num_events=int(temp1[3]);

	for i in range(0,num_events):
		thisname=temp1[5+i]
		name.append(thisname);
		time.append(get_float_time_from_name(thisname));
	counter=5+num_events;	
	for i in range(0,num_events):
		lat.append(float(temp1[counter]));
		counter+=1;
	for i in range(0,num_events):
		lon.append(float(temp1[counter]));
		counter+=1;
	for i in range(0,num_events):
		depth.append(float(temp1[counter]));
		counter+=1;	
	for i in range(0,num_events):
		mag.append(float(temp1[counter]));
		counter+=1;
	counter+=1;  # skipping over the station-with-best-coverage field. 
	for i in range(0,num_events):
		type_of_loc.append(temp1[counter]);
		counter+=1;	
	slip_rate=float(temp1[-1]);
	
	# Taking mean of only hypoDD locations
	[mean_lon, mean_lat, mean_depth] = get_average_location(line);

	return [lon, lat, time, mag, depth, type_of_loc, mean_lon, mean_lat, mean_depth, slip_rate];  


def get_average_location(line):  
# this takes the mean of available metadata, with preference for hypodd events. 
	temp=line.split()
	number_of_events=int(temp[3]);
	latitude=[]; longitude=[]; depth=[]; loc_type=[]

	for i in range(number_of_events):   # populate all the arrays with longitude, latitude, loc_type, etc. 
		latitude.append(float(temp[5+1*number_of_events + i]))
		longitude.append(float(temp[5+2*number_of_events+i]))
		depth.append(float(temp[5+3*number_of_events+i]))
		# magnitude.append(float(temp[5+4*number_of_events+i]))
		loc_type.append(temp[5+5*number_of_events+1+i].lower())

	# Taking the mean of all hypodd quantities (for plotting)
	lats_to_mean=[]
	lons_to_mean=[]
	depths_to_mean=[]
	for k in range(number_of_events):
		if loc_type[k]=="hypodd":
			lats_to_mean.append(latitude[k])
			lons_to_mean.append(longitude[k])
			depths_to_mean.append(depth[k])
	if len(lats_to_mean)>0:
		mean_lat=np.mean(lats_to_mean);
		mean_lon=np.mean(lons_to_mean);  # we have hypoDD events to use. 
		mean_depth=np.mean(depths_to_mean);
	if len(lats_to_mean)==0:
		mean_lat=np.mean(latitude);
		mean_lon=np.mean(longitude);   # no hypoDD locations; using the old one. 
		mean_depth=np.mean(depth);
	return [mean_lon, mean_lat, mean_depth]





# ------- CHRONOLOGICAL SORTING FUNCTION ------- #
def reorder_chronologically(event_names):
	""" Arrange the events in a family in chronological order """
	event_time=[];
	new_event_name=[]
	new_event_names=[]
	if len(event_names)==2:
		if event_names[0]==event_names[1]:
			return event_names;
			# This is a fix for those weird families where the same event was detected under two different event ID's.  There are only a few of them.  
	for i in range(len(event_names)):
		name=event_names[i]
		event_time.append(float(name[0:4])+float(name[5:8])/365.24+float(name[9:11])/(24*365.24)+float(name[11:13])/(24*60*365.24)+float(name[13:15])/(24*60*60*365.24))
	new_event_time=sorted(event_time)
	for i in range(len(new_event_time)):
		next_event_name=event_names[event_time.index(new_event_time[i])];
		new_event_names.append(next_event_name)
	#print new_event_names
	return new_event_names;


# ------- CALCULATE: SLIP = F(MAGNITUDE) FOR EACH EVENT ------- #
def event_slip(Magnitude):
	Mo=np.power(10,16.1+1.5*Magnitude);  # Hanks and Kanamori, 1979
	d=np.power(10,-2.36+0.17*np.log10(Mo));   # Nadeau and Johnson, 1998
	return d;



