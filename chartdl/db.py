from chartdl.config import DATABASE_URI, MUSIC_PATH

from sqlalchemy import Table, Column, String, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from datetime import datetime
import os.path

engine = create_engine(DATABASE_URI, convert_unicode=True)

Session = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)

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
    
    @property
    def constructed_path(self):
        self.construct_path(self.week, self.artist, self.title)
    
    @staticmethod
    def construct_path(week, artist, title):
        return os.path.join(MUSIC_PATH, HitlistSong.__tablename__, str(week),
                                    u'{} - {}'.format(artist, title))