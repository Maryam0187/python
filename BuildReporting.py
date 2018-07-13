#--------------------------------------------------------------------------------------
#
#     $Source: CommonTasks/BuildReporting.py $
#
#  $Copyright: (c) 2018 Bentley Systems, Incorporated. All rights reserved. $
#
#--------------------------------------------------------------------------------------
import requests, base64, os, sys, argparse, re
from requests_ntlm import HttpNtlmAuth
import matplotlib.pyplot as plt
import numpy as np
plt.style.use('ggplot')

class TFSbuild:

    #Sets the credentials
    def SetCredentials(self,username,password):
        self.username=username
        self.password=password

    #Gets the build data against the credentials 
    def buildresult(self,number): 
        if hasattr(self,"username") and hasattr(self,"password"):
            uploadapi ="http://tfs.bentley.com:8080/tfs/ProductLine/Platform%20Technology/_apis/build/builds/"+number+"?api-version=3.0"
            tfs=requests.get(uploadapi,auth=HttpNtlmAuth(self.username,self.password))
            return tfs.json()
        else:
            print "Set credentials"

    #Plots a graph for the reasons for the build failures
    def PlotGraphForFailedTasks(self,failedtask,path):
        saver, count = np.unique(np.array(failedtask), return_counts=True)
        temp=np.argsort(count)
        count=count[temp]
        saver=saver[temp]
        counts=((count/float(sum(count)))*100)
        counts=counts.round(0)
        
        bar=plt.barh(np.arange(len(saver)),count,align='center' ,color='#6E8B3D',height=0.5)
        plt.yticks(np.arange(len(saver)+1), saver,color='g')
        plt.xticks(np.arange(0, max(count)+2, step=1),color='g')
        plt.xlabel('Frequency',color='g')
        plt.title('Reasons for Failed Builds',color='g')

        i=0
        for rect in bar:
            plt.text( count[i],rect.get_y()+rect.get_height()/2.0, '%s' % str(int(counts[i]))+'%', ha='center', va='bottom',color='black') 
            i+=1    

        plt.savefig(path+"\\ReasonForBuildFailures.png",bbox_inches='tight')
        plt.close()
        
    #Plots a graph between the persons responsible for the buildfailures against the frequency of build failures    
    def FailedByGraph(self,Name,path):
        Name, count1 = np.unique(np.array(Name), return_counts=True)
        temp1=np.argsort(count1)
        count1=count1[temp1]
        Name=Name[temp1]
        counts1=((count1/float(sum(count1)))*100)
        counts1=counts1.round(0)
        
        bar=plt.barh(np.arange(len(Name)) ,count1,color='#6E8B3D',align='center',height=0.5 )
        plt.yticks(np.arange(len(Name)+1), Name,color='g')
        plt.xticks(np.arange(0, max(count1)+2, step=1),color='g')
        plt.xlabel('Frequency',color='g')
        plt.title('Failed By',color='g')

        i=0
        for rect in bar:
            plt.text(count1[i] ,rect.get_y()+rect.get_height()/2.0, '%s' % str(int(counts1[i]))+'%', ha='center', va='bottom',color='black')
            i+=1
            
        plt.savefig(path+"\\BuildFailedBy.png",bbox_inches='tight')
        plt.close()
    
    #Get the builds histoy and plots graphs for the failed builds 
    def GetResultsAndPlotGraphs(self,name,path):
        
        #---------------------------------------fetch all builds--------------------------------------
        if hasattr(self,"username") and hasattr(self,"password"): 
            uploadapi ="http://tfs.bentley.com:8080/tfs/ProductLine/Platform%20Technology/_apis/build/builds?api-version=3.0"
            tfs=requests.get(uploadapi,auth=HttpNtlmAuth(self.username,self.password))
            
            if (not tfs.ok):
                print 'Invalid username or password.'
                exit(1)
                
            dic=tfs.json()

            #-------------------------------------builds of given definition name------------------

            buildNumber=[]
            for index in dic['value']:
                if (index['definition']['name']==name):
                    buildNumber.append(index['id'])   

           #------------------------get results of builds and failed tasks of builds--------------------

            #Fails if the provided build definition doesn't matches with any of the definitions        
            if not buildNumber:
                print "The provided build definition didnt match with any of the definitions. Please provide a valid build definition. Exiting"
                exit(1)
                
            results=[]
            failedtask=[]
            failedby=[]
            
            for bn in buildNumber:
                dic=self.buildresult(str(bn))
                if (dic['status'] !='inProgress'):
                    results.append(str( dic['result'])) # result array

                url= dic['_links']['timeline']['href']
                tfs=requests.get(url,auth=HttpNtlmAuth(self.username,self.password))
                logs=tfs.json()

                for x in logs['records']:
                    
                    if "issues" in x:
                        for issuemsg in x['issues']: 
                            isusseStr=issuemsg['message']
                            m=re.search('exceeded the maximum execution time ',isusseStr)
                            if m:
                                failedtask.append('Exceed time')
                                failedby.append(str(dic['requestedFor']['displayName']))
                                print "Failed task  : Exceededs excecution time" , ". Build Number : ",bn, " Name : ",dic['requestedFor']['displayName']
                                
                    if x['result']=='failed' and "issues" in x : 
                        print "Failed task : " ,x['name'], " Build Number : ",bn, " Name : ",dic['requestedFor']['displayName']
                        failedtask.append(str(x['name']))
                        failedby.append(str(dic['requestedFor']['displayName']))

            #--------------------------------Print succeeded and failed task---------------------------------------
                        
            unique_elements, counts_elements = np.unique(np.array(results), return_counts=True)
            for x in range(len(unique_elements)):
                print unique_elements[x] , ": ",counts_elements[x]

            #---------------------------------print counts of failed task--------------------------------------- 

            unique_elements, counts_elements = np.unique(np.array(failedtask), return_counts=True)
            for x in range(len(unique_elements)):
                print unique_elements[x] , ": ",counts_elements[x]

            print "Build Numbers of given definition: ",buildNumber
            print
            if failedtask:
                self.PlotGraphForFailedTasks(failedtask,path)
            if failedby:
                self.FailedByGraph(failedby,path)
         

parser = argparse.ArgumentParser()

parser.add_argument("--userName", help="UserName for logging", required=True)
parser.add_argument("--password", help="Password for logging", required=True)
parser.add_argument("--buildDefinition", help="Specify the build definition against which you want to check the history", required=True)
parser.add_argument("--workspaceRoot", help="Specify the folder where you want the build history graphs", required=True)

args = parser.parse_args()
    
UserName = args.userName
Password = args.password
BuildDef = args.buildDefinition
WorkspaceRoot = args.workspaceRoot

#Verify if the workspace is a valid path
if (not os.path.exists(WorkspaceRoot)):
    print 'Please provide a valid directory path.'
    exit(1)
    
item = TFSbuild()
item.SetCredentials(UserName, Password)
item.GetResultsAndPlotGraphs(BuildDef,WorkspaceRoot)

