import pytest
from neurovolume.privacy import private_output


def test_system_private_is_not_project_private(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert private_output("private/cohort.csv") == tmp_path / "private/cohort.csv"
    for path in ["public/cohort.csv", "private/../public/cohort.csv", "/private/tmp/cohort.csv"]:
        with pytest.raises(ValueError): private_output(path)


def test_symlink_cannot_redirect_private_outputs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "private").mkdir()
    (tmp_path / "public").mkdir()
    (tmp_path / "private/escape").symlink_to(tmp_path / "public", target_is_directory=True)
    with pytest.raises(ValueError): private_output("private/escape/cohort.csv")


def test_private_root_cannot_be_symlink(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "public").mkdir()
    (tmp_path / "private").symlink_to(tmp_path / "public", target_is_directory=True)
    with pytest.raises(ValueError): private_output("private/cohort.csv")
