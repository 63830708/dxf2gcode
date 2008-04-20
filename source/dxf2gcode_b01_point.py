#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_b01_dxf_import
#Programmer: Christian Kohl�ffel
#E-mail:     n/A
#
#Copyright 2008 Christian Kohl�ffel
#
#Distributed under the terms of the GPL (GNU Public License)
#
#dxf2gcode is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 2 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# About Dialog
# First Version of dxf2gcode_b01 Hopefully all works as it should

from math import sqrt, sin, cos, atan2, radians, degrees

class PointClass:
    def __init__(self,x=0,y=0):
        self.x=x
        self.y=y
    def __str__(self):
        return ('\nPoint:   X ->%6.2f  Y ->%6.2f' %(self.x,self.y))
    def __cmp__(self, other) : 
      return (self.x == other.x) and (self.y == other.y)
    def __add__(self, other): # add to another point
        return PointClass(self.x+other.x, self.y+other.y)
    def __rmul__(self, other):
        return PointClass(other * self.x,  other * self.y)
    def distance(self,other):
        return sqrt(pow(self.x-other.x,2)+pow(self.y-other.y,2))
    def isintol(self,other,tol):
        return (abs(self.x-other.x)<=tol) & (abs(self.y-other.y)<tol)
    def triangle_height(self,other1,other2):
        #Die 3 L�ngen des Dreiecks ausrechnen
        a=self.distance(other1)
        b=other1.distance(other2)
        c=self.distance(other2)
        print a
        print b
        print c
        
        return sqrt(pow(b,2)-pow((pow(c,2)+pow(b,2)-pow(a,2))/(2*c),2))                
      
class PointsClass:
    #Initialisieren der Klasse
    def __init__(self,point_nr=0, geo_nr=0,Layer_Nr=None,be=[],en=[],be_cp=[],en_cp=[]):
        self.point_nr=point_nr
        self.geo_nr=geo_nr
        self.Layer_Nr=Layer_Nr
        self.be=be
        self.en=en
        self.be_cp=be_cp
        self.en_cp=en_cp
        
    
    #Wie die Klasse ausgegeben wird.
    def __str__(self):
        # how to print the object
        return '\npoint_nr ->'+str(self.point_nr)+'\ngeo_nr ->'+str(self.geo_nr) \
               +'\nLayer_Nr ->'+str(self.Layer_Nr)\
               +'\nbe ->'+str(self.be)+'\nen ->'+str(self.en)\
               +'\nbe_cp ->'+str(self.be_cp)+'\nen_cp ->'+str(self.en_cp)

class ContourClass:
    #Initialisieren der Klasse
    def __init__(self,cont_nr=0,closed=0,order=[],length=0):
        self.cont_nr=cont_nr
        self.closed=closed
        self.order=order
        self.length=length
        

    #Komplettes umdrehen der Kontur
    def reverse(self):
        self.order.reverse()
        for i in range(len(self.order)):
            if self.order[i][1]==0:
                self.order[i][1]=1
            else:
                self.order[i][1]=0
        return

    #Ist die klasse geschlossen wenn ja dann 1 zur�ck geben
    def is_contour_closed(self):

        #Immer nur die Letzte �berpr�fen da diese neu ist        
        for j in range(len(self.order)-1):
            if self.order[-1][0]==self.order[j][0]:
                if j==0:
                    self.closed=1
                    return self.closed
                else:
                    self.closed=2
                    return self.closed
        return self.closed


    #Ist die klasse geschlossen wenn ja dann 1 zur�ck geben
    def remove_other_closed_contour(self):
        for i in range(len(self.order)):
            for j in range(i+1,len(self.order)):
                #print '\ni: '+str(i)+'j: '+str(j)
                if self.order[i][0]==self.order[j][0]:
                   self.order=self.order[0:i]
                   break
        return 
    #Berechnen der Zusammengesetzen Kontur L�nge
    def calc_length(self,geos=None):        
        #Falls die beste geschlossen ist und erste Geo == Letze dann entfernen
        if (self.closed==1) & (len(self.order)>1):
            if self.order[0]==self.order[-1]:
                del(self.order[-1])

        self.length=0
        for i in range(len(self.order)):
            self.length+=geos[self.order[i][0]].length
        return


    
    def analyse_and_opt(self,geos=None):
        #Errechnen der L�nge
        self.calc_length(geos)
        
        #Optimierung f�r geschlossene Konturen
        if self.closed==1:
            summe=0
            #Berechnung der Fl�ch nach Gau�-Elling Positive Wert bedeutet CW
            #negativer Wert bedeutet CCW geschlossenes Polygon
            geo_point_l, dummy=geos[self.order[-1][0]].get_start_end_points(self.order[-1][1])            
            for geo_order_nr in range(len(self.order)):
                geo_point, dummy=geos[self.order[geo_order_nr][0]].get_start_end_points(self.order[geo_order_nr][1])
                summe+=(geo_point_l.x*geo_point.y-geo_point.x*geo_point_l.y)/2
                geo_point_l=geo_point
            if summe>0.0:
                self.reverse()

            #Suchen des kleinsten Startpunkts von unten Links X zuerst (Muss neue Schleife sein!)
            min_point=geo_point_l
            min_point_nr=None
            for geo_order_nr in range(len(self.order)):
                geo_point, dummy=geos[self.order[geo_order_nr][0]].get_start_end_points(self.order[geo_order_nr][1])
                #Geringster Abstand nach unten Unten Links
                if (min_point.x+min_point.y)>=(geo_point.x+geo_point.y):
                    min_point=geo_point
                    min_point_nr=geo_order_nr
            #Kontur so anordnen das neuer Startpunkt am Anfang liegt
            self.set_new_startpoint(min_point_nr)
            
        #Optimierung f�r offene Konturen
        else:
            geo_spoint, dummy=geos[self.order[0][0]].get_start_end_points(self.order[0][1])
            geo_epoint, dummy=geos[self.order[0][0]].get_start_end_points(not(self.order[0][1]))
            if (geo_spoint.x+geo_spoint.y)>=(geo_epoint.x+geo_epoint.y):
                self.reverse()


    #Neuen Startpunkt an den Anfang stellen
    def set_new_startpoint(self,st_p):
        self.order=self.order[st_p:len(self.order)]+self.order[0:st_p]
        
    #Wie die Klasse ausgegeben wird.
    def __str__(self):
        # how to print the object
        return '\ncont_nr ->'+str(self.cont_nr)+'\nclosed ->'+str(self.closed) \
               +'\norder ->'+str(self.order)+'\nlength ->'+str(self.length)