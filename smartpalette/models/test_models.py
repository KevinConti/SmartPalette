import pytest
from sqlalchemy.orm import scoped_session, sessionmaker

from smartpalette.models.models import User, Image, Palette, Color
from sqlalchemy import create_engine


@pytest.fixture(scope="module")
def session():
    engine = create_engine('postgres://postgres:password@localhost:5432/test_local_database')
    db_session = scoped_session(sessionmaker(autocommit=False,
                                             autoflush=False,
                                             bind=engine))
    yield db_session
    # db_session.close()


# User

def test_create_user(session):

    kevin = User("kevin", "password")
    session.add(kevin)
    session.commit()
    result = session.query(User).filter(User.username == 'kevin').first()
    assert result == kevin
    session.delete(result)
    session.commit()
    user = session.query(User).filter(User.username == 'kevin').first()
    assert user is None


def test_user_has_picture(session):
    try:
        devan = User("devan", "password")
        devans_image = Image(filepath="/awesomesauce", username="devan")
        devans_palette = Palette(image=devans_image)
        session.add(devan)
        session.add(devans_image)
        session.add(devans_palette)
        session.commit()
        image = session.query(User).filter(User.username == 'devan').first().images[0]
        assert image == devans_image
        session.delete(devan)
        session.delete(devans_image)
        session.delete(devans_palette)
        session.commit()
    except:
        assert False
