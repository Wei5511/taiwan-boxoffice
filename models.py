from typing import Optional
from datetime import date
from sqlmodel import Field, SQLModel, Relationship

class Movie(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # 中文片名
    release_date: Optional[date] = None # 上映日
    country: Optional[str] = None # 國別
    distributor: Optional[str] = None # 出品
    
    # Relationship
    weekly_records: list["WeeklyBoxOffice"] = Relationship(back_populates="movie")
    daily_showtimes: list["DailyShowtime"] = Relationship(back_populates="movie")

class WeeklyBoxOffice(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    movie_id: int = Field(foreign_key="movie.id")
    
    report_date_start: date
    report_date_end: date
    
    theater_count: Optional[int] = None # 院數
    weekly_revenue: Optional[int] = None # 金額 (Need cleaning)
    cumulative_revenue: Optional[int] = None # 總金額 (Need cleaning)
    weekly_tickets: Optional[int] = None # 票數 (Need cleaning)
    cumulative_tickets: Optional[int] = None # 累積票數 (Need cleaning)
    
    # Relationship
    movie: Optional[Movie] = Relationship(back_populates="weekly_records")

class DailyShowtime(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    movie_id: int = Field(foreign_key="movie.id")
    
    date: date
    region: str # e.g. "Taipei", "Kaohsiung"
    showtime_count: int
    
    # Relationship
    movie: Optional[Movie] = Relationship(back_populates="daily_showtimes")
