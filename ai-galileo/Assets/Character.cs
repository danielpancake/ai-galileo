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
    private AnimatorController m_animatorController;

    private AnimationState m_animationState = AnimationState.Idle;

    public float m_speed = 5f;
    public float m_jumpAmount = 5f;

    public Transform groundCheck;
    public LayerMask ground;

    void Start()
    {
        m_rigidbody = GetComponent<Rigidbody>();
        m_animatorController = GetComponent<AnimatorController>();
    }

    bool IsGrounded()
    {
        return Physics.CheckSphere(groundCheck.position, .1f, ground);
    }

    void Update()
    {
        Vector3 _v = new(Input.GetAxis("Horizontal"), 0, Input.GetAxis("Vertical"));
        m_rigidbody.MovePosition(transform.position + _v * Time.deltaTime * m_speed);

        if (Input.GetKeyDown(KeyCode.Space) && IsGrounded())
        {
            m_rigidbody.AddForce(Vector3.up * m_jumpAmount, ForceMode.Impulse);
        }

        Debug.Log(m_rigidbody.velocity.y);

        transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(_v), Time.deltaTime * 40f);
    }
}
