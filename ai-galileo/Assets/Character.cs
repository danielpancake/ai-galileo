using System;
using System.Collections;
using System.Collections.Generic;
using UnityEditor.Animations;
using UnityEngine;

enum AnimationState
{
    Fall,
    Idle,
    Jump,
    Run,
    Sprint,
    Strafe,
    Talk,
    Walk,
}

public class Character : MonoBehaviour
{
    private Rigidbody m_rigidbody;
    private Animator m_animator;

    private AnimationState m_animationState = AnimationState.Idle;

    public float m_maxSpeed = 10f;
    public float m_jumpAmount = 5f;

    public Transform groundCheck;
    public LayerMask ground;

    public RuntimeAnimatorController anim_fall;
    public RuntimeAnimatorController anim_idle;
    public RuntimeAnimatorController anim_jump;
    public RuntimeAnimatorController anim_run;
    public RuntimeAnimatorController anim_sprint;
    public RuntimeAnimatorController anim_strafe;
    public RuntimeAnimatorController anim_talk;
    public RuntimeAnimatorController anim_walk;

    private bool has_jumped = false;

    void Start()
    {
        m_rigidbody = GetComponent<Rigidbody>();
        m_animator = GetComponent<Animator>();
    }

    bool IsGrounded()
    {
        return Physics.CheckSphere(groundCheck.position, .1f, ground);
    }

    void Update()
    {
        Vector3 _v = new(Input.GetAxis("Horizontal"), 0, Input.GetAxis("Vertical"));
        m_rigidbody.MovePosition(transform.position + _v * Time.deltaTime * m_maxSpeed);

        if (IsGrounded())
        {
            has_jumped = false;

            if (Input.GetKeyDown(KeyCode.Space))
            {
                m_rigidbody.AddForce(Vector3.up * m_jumpAmount, ForceMode.Impulse);
                has_jumped = true;
            }
        }

        if (_v.magnitude != 0)
        {
            m_rigidbody.rotation = Quaternion.Slerp(m_rigidbody.rotation, Quaternion.LookRotation(_v), Time.deltaTime * 40f);
        }

        UpdateAnimationState();
        SetAnimation(m_animationState);
    }

    void UpdateAnimationState()
    {
        if (IsGrounded())
        {
            float _m = m_rigidbody.velocity.magnitude;
            if (_m > .75f)
            {
                m_animationState = AnimationState.Run;
            }
            else if (_m > .5f)
            {
                m_animationState = AnimationState.Sprint;
            }
            else if (_m > .25f)
            {
                m_animationState = AnimationState.Walk;
            }
            else
            {
                m_animationState = AnimationState.Idle;
            }
        }
        else
        {
            m_animationState = has_jumped ? AnimationState.Fall : AnimationState.Jump;
        }
    }

    void SetAnimation(AnimationState state)
    {
        RuntimeAnimatorController _a = anim_idle;
        switch (state)
        {
            case AnimationState.Fall: _a = anim_jump; break;
            case AnimationState.Idle: _a = anim_idle; break;
            case AnimationState.Jump: _a = anim_fall; break;
            case AnimationState.Run: _a = anim_run; break;
            case AnimationState.Sprint: _a = anim_sprint; break;
            case AnimationState.Strafe: _a = anim_strafe; break;
            case AnimationState.Talk: _a = anim_talk; break;
            case AnimationState.Walk: _a = anim_walk; break;
        }

        m_animator.runtimeAnimatorController = _a;
    }
}
