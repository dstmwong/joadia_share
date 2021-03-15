# -*- coding: utf-8 -*-
"""
Created on Tue Jul 24 14:51:37 2018
Original scenario definition of the JOADIA map.
This functionality now resides in the core.environment module.
@author: wongm
"""

from core.model import Surface, Territory, POD, Population

#definition of the land/sea/air mass
def create_scenario():
    surface_list = list()
    territory_list = list()
    
    l1 = Surface(Surface.LAND, 3)
    l1.x = 87
    l1.y = 717
    
    surface_list.append(l1)
    
    s1 = Surface(Surface.WATER)
    s1.x = 125
    s1.y = 660
    surface_list.append(s1)
    
    a1 = Surface(Surface.AIR)
    a1.x = 87
    a1.y = 717
    surface_list.append(a1)
    
    
    t1 = Territory("T1", l1, s1, a1)
    territory_list.append(t1)
    t1.create_population(Population.VILLAGE)
        
    #----------------------------------
    
    
    l2 = Surface(Surface.LAND, 3)
    l2.x = 230
    l2.y = 550
    
    surface_list.append(l2)
    
    s2 = Surface(Surface.WATER)
    s2.x = 160
    s2.y = 600
    surface_list.append(s2)
    
    a2 = Surface(Surface.AIR)
    a2.x = 230
    a2.y = 550
    surface_list.append(a2)
    
    t2 = Territory("T2", l2, s2, a2)
    territory_list.append(t2)
    t2.create_population(Population.VILLAGE)
     
    s1.connect(s2)
    a1.connect(a2)
    
    #---------------------------------------
    
    l3 = Surface(Surface.LAND, 2)
    l3.x = 325
    l3.y = 500
   
    surface_list.append(l3)
    
    s3 = Surface(Surface.WATER)
    s3.x = 400
    s3.y = 470
    surface_list.append(s3)
    
    a3 = Surface(Surface.AIR)
    a3.x = 325
    a3.y = 500
    surface_list.append(a3)
    
    t3 = Territory("T3", l3, s3, a3)
    territory_list.append(t3)
    t3.create_population(Population.CITY)
    
    s2.connect(s3)
    l2.connect(l3)
    a2.connect(a3)
    
    #---------------------------------------
    
    l4 = Surface(Surface.LAND, 1)
    l4.x = 190
    l4.y = 395
    surface_list.append(l4)
    
    s4_1 = Surface(Surface.WATER)
    s4_1.x = 75
    s4_1.y = 425
    surface_list.append(s4_1)
    
    s4_2 = Surface(Surface.WATER)
    s4_2.x = 270
    s4_2.y = 340
    surface_list.append(s4_2)
    
    a4 = Surface(Surface.AIR)
    a4.x = 190
    a4.y = 395
    surface_list.append(a4)
    
    t4 = Territory("T4", l4, [s4_1, s4_2], a4)
    t4.add_pod(POD(POD.AIR))
    territory_list.append(t4)
    
    l2.connect(l4)
    l3.connect(l4)
    s2.connect(s4_1)
    s3.connect(s4_2)
    a2.connect(a4)
    a3.connect(a4)
    
    #-------------------------------------
    
    l5 = Surface(Surface.LAND, 3)
    l5.x = 470
    l5.y = 600
    surface_list.append(l5)
    
    s5 = Surface(Surface.WATER)
    s5.x = 521
    s5.y = 698
    surface_list.append(s5)
    
    a5 = Surface(Surface.AIR)
    a5.x = 470
    a5.y = 600
    surface_list.append(a5)
    
    t5 = Territory("T5", l5, s5, a5)
    territory_list.append(t5)
    t5.create_population(Population.CITY)
    
    s3.connect(s5)
    a3.connect(a5)
    
    #--------------------------------------
    l6 = Surface(Surface.LAND, 3)
    l6.x = 380
    l6.y = 700
    surface_list.append(l6)
    
    s6 = Surface(Surface.WATER)
    s6.x = 300
    s6.y = 750
    surface_list.append(s6)
    
    a6 = Surface(Surface.AIR)
    a6.x = 380
    a6.y = 700
    surface_list.append(a6)
    
    t6 = Territory("T6", l6, s6, a6)
    territory_list.append(t6)
    t6.create_population(Population.TOWN)
    
    l5.connect(l6)
    s5.connect(s6)
    s2.connect(s6)
    a5.connect(a6)
    a2.connect(a6)
    
    #--------------------------------------
    
    l7 = Surface(Surface.LAND, 1)
    l7.x = 540
    l7.y = 475
    surface_list.append(l7)
    
    s7 = Surface(Surface.WATER)
    s7.x = 565
    s7.y = 552
    surface_list.append(s7)
    
    s7_b = Surface(Surface.WATER)
    s7_b.x = 508
    s7_b.y = 419
    surface_list.append(s7_b) 
    
    a7 = Surface(Surface.AIR)
    a7.x = 540
    a7.y = 475
    surface_list.append(a7)
    
    t7 = Territory("T7", l7, [s7, s7_b], a7)
    t7.add_pod(POD(POD.AIR))
    t7.add_pod(POD(POD.SEA))
    territory_list.append(t7)
    
    s5.connect(s7)
    a5.connect(a7)
    
    #--------------------------------------
    
    l8 = Surface(Surface.LAND, 1)
    l8.x = 433
    l8.y = 374
    
    s8 = Surface(Surface.WATER)
    s8.x = 355
    s8.y = 383
   
    a8 = Surface(Surface.AIR)
    a8.x = 433
    a8.y = 374
    
    t8 = Territory("T8", l8, [s8, s7_b], a8)
    t8.create_population(Population.CITY)
    territory_list.append(t8)
    
    l7.connect(l8)
    a7.connect(a8)
    s7.connect(s8)
    s3.connect(s8)
    a3.connect(a8)
    
    #--------------------------------------
    
    l9 = Surface(Surface.LAND, 1)
    l9.x = 684
    l9.y = 541
    
    s9 = Surface(Surface.WATER)
    s9.x = 671
    s9.y = 616
   
    a9 = Surface(Surface.AIR)
    a9.x = 684
    a9.y = 541
    
    t9 = Territory("T9", l9, s9, a9)
    t9.create_population(Population.CITY)
    territory_list.append(t9)
    
    l7.connect(l9)
    a7.connect(a9)
    s7.connect(s9)
    
    
    #--------------------------------------
    
    l10 = Surface(Surface.LAND, 1)
    l10.x = 691
    l10.y = 436
    
    s10 = Surface(Surface.WATER)
    s10.x = 680
    s10.y = 392
   
    a10 = Surface(Surface.AIR)
    a10.x = 691
    a10.y = 436
    
    t10 = Territory("T10", l10, s10, a10)
    t10.create_population(Population.TOWN)
    territory_list.append(t10)
    
    l9.connect(l10)
    l7.connect(l10)
    a9.connect(a10)
    a7.connect(a10)
    s7_b.connect(s10)
    
    #--------------------------------------
    
    l11 = Surface(Surface.LAND, 3)
    l11.x = 849
    l11.y = 422
    
    s11 = Surface(Surface.WATER)
    s11.x = 932
    s11.y = 371
   
    a11 = Surface(Surface.AIR)
    a11.x = 849
    a11.y = 422
    
    t11 = Territory("T11", l11, s11, a11)
    t11.create_population(Population.VILLAGE)
    territory_list.append(t11)
    
    l10.connect(l11)
    a10.connect(a11)
    s10.connect(s11)
    
    #--------------------------------------
    
    l12 = Surface(Surface.LAND, 3)
    l12.x = 840
    l12.y = 545
    
    s12 = Surface(Surface.WATER)
    s12.x = 974
    s12.y = 572
    
    s12_b = Surface(Surface.WATER)
    s12_b.x = 859
    s12_b.y = 681
   
    a12 = Surface(Surface.AIR)
    a12.x = 840
    a12.y = 545
    
    t12 = Territory("T12", l12, [s12, s12_b], a12)
    t12.create_population(Population.CITY)
    territory_list.append(t12)
    
    l11.connect(l12) 
    l9.connect(l12)
    a11.connect(a12)
    a9.connect(a12)
    s11.connect(s12)
    s9.connect(s12_b)
    s12.connect(s12_b)
   
    #--------------------------------------
    
    l13 = Surface(Surface.LAND, 3)
    l13.x = 903
    l13.y = 609
   
    a13 = Surface(Surface.AIR)
    a13.x = 903
    a13.y = 609
    
    t13 = Territory("T13", l13, [s12, s12_b], a13)
    t13.create_population(Population.VILLAGE)
    territory_list.append(t13)
    
    l12.connect(l13)
    a12.connect(a13)
    
    #--------------------------------------
    
    l14 = Surface(Surface.LAND, 3)
    l14.x = 365
    l14.y = 286
    
    s14 = Surface(Surface.WATER)
    s14.x = 311
    s14.y = 313
    
    a14 = Surface(Surface.AIR)
    a14.x = 365
    a14.y = 286
    
    t14 = Territory("T14", l14, s14, a14)
    t14.create_population(Population.TOWN)
    territory_list.append(t14)
    
    l8.connect(l14)
    a8.connect(a14)
    s8.connect(s14)
    s4_2.connect(s14)
    a4.connect(a14)
    
    #--------------------------------------
    
    l15 = Surface(Surface.LAND, 2)
    l15.x = 482
    l15.y = 282
    
    s15 = Surface(Surface.WATER)
    s15.x = 544
    s15.y = 301
    
    a15 = Surface(Surface.AIR)
    a15.x = 482
    a15.y = 282
    
    t15 = Territory("T15", l15, s15, a15)
    t15.create_population(Population.CITY)
    territory_list.append(t15)
    
    l14.connect(l15)
    l8.connect(l15)       #NOTE: added
    a14.connect(a15)
    a8.connect(a15)       #NOTE: added
    s7_b.connect(s15)
    
    
    #--------------------------------------
    
    l16 = Surface(Surface.LAND, 3)
    l16.x = 117
    l16.y = 285
    
    s16 = Surface(Surface.WATER)
    s16.x = 31
    s16.y = 259
    
    a16 = Surface(Surface.AIR)
    a16.x = 117
    a16.y = 285
    
    t16 = Territory("T16", l16, s16, a16)
    t16.create_population(Population.VILLAGE)
    territory_list.append(t16)
    
    l4.connect(l16)
    a4.connect(a16)
    s4_1.connect(s16)
    
    #--------------------------------------
    
    l17 = Surface(Surface.LAND, 2)
    l17.x = 180
    l17.y = 242
    
    s17 = Surface(Surface.WATER)
    s17.x = 172
    s17.y = 183
    
    a17 = Surface(Surface.AIR)
    a17.x = 180
    a17.y = 242
    
    t17 = Territory("T17", l17, s17, a17)
    t17.create_population(Population.TOWN)
    territory_list.append(t17)
    
    l16.connect(l17)
    l4.connect(l17)
    a16.connect(a17)      #NOTE: fixed
    a4.connect(a17)       #NOTE: fixed
    s4_2.connect(s17)
    s16.connect(s17)
    
    
    #--------------------------------------
    
    l18 = Surface(Surface.LAND, 1)
    l18.x = 313
    l18.y = 189
    
    s18 = Surface(Surface.WATER)
    s18.x = 242
    s18.y = 204
    
    s18_b = Surface(Surface.WATER)
    s18_b.x = 308
    s18_b.y = 26
    
    a18 = Surface(Surface.AIR)
    a18.x = 313
    a18.y = 189
    
    t18 = Territory("T18", l18, [s18, s18_b], a18)
    t18.create_population(Population.TOWN)
    territory_list.append(t18)
    
    l14.connect(l18)
    a14.connect(a18)
    s17.connect(s18)
    s14.connect(s18)
    s18.connect(s18_b)
    a17.connect(a18)
    
    
    #--------------------------------------
    
    l19 = Surface(Surface.LAND, 2)
    l19.x = 474
    l19.y = 167
    
    s19 = Surface(Surface.WATER)
    s19.x = 483
    s19.y = 101
    
    a19 = Surface(Surface.AIR)
    a19.x = 474
    a19.y = 167
    
    t19 = Territory("T19", l19, s19, a19)
    t19.create_population(Population.TOWN)
    territory_list.append(t19)
    
    t18.connect(t19)
    t15.connect(t19)
    s18_b.connect(s19)
    
    #--------------------------------------
    
    l20 = Surface(Surface.LAND, 2)
    a20 = Surface(Surface.AIR)
    
    s20 = Surface(Surface.WATER)
    s20.x = 609
    s20.y = 72
    
    s20_b = Surface(Surface.WATER)
    s20_b.x = 622
    s20_b.y = 244
    
    t20 = Territory("T20", l20, [s20, s20_b], a20)
    t20.create_population(Population.TOWN)
    t20.set_position(601, 150)
    territory_list.append(t20)
    
    t19.connect(t20)
    s19.connect(s20)
    s15.connect(s20_b)
    
    #--------------------------------------
    
    l21 = Surface(Surface.LAND, 3)
    a21 = Surface(Surface.AIR)
    
    s21 = Surface(Surface.WATER)
    s21.x = 778
    s21.y = 132
    
    t21 = Territory("T21", l21, s21, a21)
    t21.create_population(Population.TOWN)
    t21.set_position(704, 167)
    territory_list.append(t21)
    
    t20.connect(t21)
    s20.connect(s21)
    s20_b.connect(s21)
    
    #--------------------------------------
    
    l22 = Surface(Surface.LAND, 3)
    a22 = Surface(Surface.AIR)
    
    s22 = Surface(Surface.WATER)
    s22.x = 101
    s22.y = 151
    
    t22 = Territory("T22", l22, s22, a22)
    t22.create_population(Population.VILLAGE)
    t22.set_position(105, 108)
    territory_list.append(t22)
    
    s16.connect(s22)
    s17.connect(s22)
    a16.connect(a22)
    a17.connect(a22)
    
    #--------------------------------------
    
    l23 = Surface(Surface.LAND, 1)
    a23 = Surface(Surface.AIR)
    
    
    t23 = Territory("T23", l23, s18_b, a23)
    t23.create_population(Population.VILLAGE)
    t23.set_position(303, 76)
    territory_list.append(t23)
    
    t18.connect(t23)
   
    
    return territory_list

