from __future__ import unicode_literals

from sqlalchemy import Table, Column, String, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base

from datetime import datetime
import os.path

Base = declarative_base() 


class HitlistSong(Base):
    __tablename__ = 'hitlist'
    
    artist = Column(String, nullable=False)
    title = Column(String, nullable=False)
    image_url = Column(String, default='')
    position = Column(Integer, primary_key=True)
    last_position = Column(Integer, default=-1)
    week = Column(Integer, primary_key=True)
    downloaded = Column(Boolean, default=False)
    path = Column(String)
    video_id = Column(String)

    @classmethod
    def from_chart(cls, chart, downloaded=False):
        week = datetime.now().isocalendar()[1]
        artist = chart['artist']
        title = chart['title']
        image_url = chart['image']['src']
        position = chart['position']
        last_position = chart['last_position']
        
        return cls(artist=artist, title=title, image_url=image_url,
                   position=position, last_position=last_position,
                   week=week, downloaded=downloaded,
                   path=cls.construct_path(week, artist, title))
    
    def rebuild_path(self):
        self.path = self.construct_path(self.week, self.artist, self.title)
    
    @property
    def constructed_path(self):
        self.construct_path(self.week, self.artist, self.title)
    
    @staticmethod
    def construct_path(week, artist, title):
        return os.path.join(HitlistSong.__tablename__, unicode(week),
                                    u'{} - {}'.format(artist.replace('/', ' '),
                                                      title.replace('/', ' ')))

    def __eq__(self, other):
        if isinstance(other, dict):
            return all(getattr(self, value) == other.get('value') for value in
                       ['artist', 'title', 'position', 'last_position'])
        else:
            return Base.__eq__(self, other)
    
    def __ne__(self, other):
        if isinstance(other, dict):
            return not self == other
        else:
            return Base.__ne__(self, other)


    def __unicode__(self):
        return '{self.artist} - {self.title}'.format(self=self)
    
    def __str__(self):
        return self.__unicode__().encode('utf-8')