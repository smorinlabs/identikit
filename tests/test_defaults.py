"""Tests for identikit.defaults — git-conditional "to" default derivation (D2b)."""

from __future__ import annotations

from identikit import common, defaults


def _config():
    return common.Config(
        identity={
            "repo_name": common.IdentityField(
                "repo_name", "py-launch-blueprint", "repo_name", derive="origin.repo"
            ),
            "owner": common.IdentityField(
                "owner", "smorinlabs", "github_owner", derive="origin.owner"
            ),
            "package_name": common.IdentityField(
                "package_name",
                "py_launch_blueprint",
                "python_identifier",
                derive="repo_name|snake",
            ),
            "author": common.IdentityField(
                "author", "Steve Morin", "", derive="git.user.name"
            ),
        },
        guard=common.GuardConfig(skip_if_origin=("smorinlabs/py-launch-blueprint",)),
    )


def test_derive_resolves_regardless_of_field_order():
    # package_name references repo_name but is listed FIRST — must still resolve.
    cfg = common.Config(
        identity={
            "package_name": common.IdentityField(
                "package_name",
                "py_launch_blueprint",
                "python_identifier",
                derive="repo_name|snake",
            ),
            "repo_name": common.IdentityField(
                "repo_name", "py-launch-blueprint", "repo_name", derive="origin.repo"
            ),
        },
        guard=common.GuardConfig(skip_if_origin=("smorinlabs/py-launch-blueprint",)),
    )
    ctx = defaults.context_from_git(
        cfg, "git@github.com:acme/payments-api.git", "A", "a@e.co"
    )
    out = defaults.derive_defaults(cfg, ctx)
    assert out["repo_name"] == "payments-api"
    assert out["package_name"] == "payments_api"


def test_template_button_mode_derives_from_origin():
    # mode 1/2: origin is the new repo → prefill owner/repo, derive package, author.
    ctx = defaults.context_from_git(
        _config(),
        origin_url="git@github.com:acme/payments-api.git",
        user_name="Ada Lovelace",
        user_email="ada@example.com",
    )
    out = defaults.derive_defaults(_config(), ctx)
    assert out["repo_name"] == "payments-api"
    assert out["owner"] == "acme"
    assert out["package_name"] == "payments_api"  # repo_name|snake
    assert out["author"] == "Ada Lovelace"


def test_fork_mode_suppresses_colliding_repo_name():
    # mode 4: fork origin = <forker>/py-launch-blueprint. owner derives to the
    # forker (fine), but repo_name would collide with the FROM value → suppress.
    ctx = defaults.context_from_git(
        _config(),
        origin_url="git@github.com:forker/py-launch-blueprint.git",
        user_name="F",
        user_email="f@e.co",
    )
    out = defaults.derive_defaults(_config(), ctx)
    assert out["repo_name"] == ""  # collides with FROM → no suggestion
    assert out["owner"] == "forker"


def test_blueprint_origin_is_skipped_entirely():
    # origin points at the template itself → don't derive owner/repo from it.
    ctx = defaults.context_from_git(
        _config(),
        origin_url="git@github.com:smorinlabs/py-launch-blueprint.git",
        user_name="X",
        user_email="x@e.co",
    )
    assert ctx.origin_owner is None
    assert ctx.origin_repo is None
    out = defaults.derive_defaults(_config(), ctx)
    assert out["owner"] == ""
    assert out["repo_name"] == ""


def test_clone_reinit_mode_no_origin():
    # mode 3: no origin → git-config fields still derive; origin fields empty.
    ctx = defaults.context_from_git(
        _config(), origin_url="", user_name="Grace", user_email="g@e.co"
    )
    out = defaults.derive_defaults(_config(), ctx)
    assert out["owner"] == ""
    assert out["repo_name"] == ""
    assert out["author"] == "Grace"
