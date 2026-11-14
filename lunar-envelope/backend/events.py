"""Bracketed, approximate threshold windows, independent of display bin size.

A fixed scan can miss crossings between equal-sign samples, grazing contacts,
short windows and excursions. Tolerance is numerical, not an accuracy claim.
"""
from datetime import timedelta

def threshold_windows(start,end,scan,elevation,threshold):
    """Return disjoint intervals and detected transitions for elevation > threshold."""
    if end<start or scan.total_seconds()<=0: raise ValueError('Invalid scan interval')
    def above(t):return elevation(t)>threshold
    left=start; left_state=above(left)
    opening=start if left_state else None
    windows=[];transitions=[]
    while left<end:
        right=min(left+scan,end);right_state=above(right)
        if left_state!=right_state:
            lo,hi=left,right
            while (hi-lo).total_seconds()>1:
                mid=lo+(hi-lo)/2
                if above(mid)==left_state:lo=mid
                else:hi=mid
            crossing=lo+(hi-lo)/2
            transitions.append({'time':crossing,'kind':'rise' if right_state else 'set'})
            if right_state:opening=crossing
            elif opening is not None:
                if crossing>opening:windows.append((opening,crossing))
                opening=None
        left=right;left_state=right_state
    if opening is not None and end>opening:windows.append((opening,end))
    return windows,transitions

def intersect(a,b):
    result=[];i=j=0
    while i<len(a) and j<len(b):
        start=max(a[i][0],b[j][0]);end=min(a[i][1],b[j][1])
        if start<end: result.append((start,end))
        if a[i][1]<b[j][1]:i+=1
        else:j+=1
    return result
