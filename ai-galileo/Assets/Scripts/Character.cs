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
    private Rigidbody rb;
    private Animator animator;

    public Transform groundCheck;
    public LayerMask ground;

    // Movement speed
    public float walkSpeed = 8f;
    public float runSpeed = 12f;
    public float sprintSpeed = 15f;

    public float jumpAmount = 5f;

    public float acceleration = 5f;

    private float currentSpeed;

    // Input keyboard
    private float verticalInput;
    private float horizontalInput;

    private bool has_jumped = false;

    // Animation handler
    private AnimationState animationState = AnimationState.Idle;

    public RuntimeAnimatorController anim_fall;
    public RuntimeAnimatorController anim_idle;
    public RuntimeAnimatorController anim_jump;
    public RuntimeAnimatorController anim_run;
    public RuntimeAnimatorController anim_sprint;
    public RuntimeAnimatorController anim_strafe;
    public RuntimeAnimatorController anim_talk;
    public RuntimeAnimatorController anim_walk;

    void Start()
    {
        rb = GetComponent<Rigidbody>();
        animator = GetComponent<Animator>();

        currentSpeed = walkSpeed;
    }

    bool IsGrounded()
    {
        return Physics.CheckSphere(groundCheck.position, .1f, ground);
    }

    void Update()
    {
        verticalInput = Input.GetAxis("Vertical");
        horizontalInput = Input.GetAxis("Horizontal");

        Vector3 input = new (horizontalInput, 0, verticalInput);
        input.Normalize();

        if (input.magnitude > 0)
        {
            currentSpeed = Mathf.MoveTowards(currentSpeed, sprintSpeed, acceleration * Time.deltaTime);
            rb.rotation = Quaternion.Slerp(rb.rotation, Quaternion.LookRotation(input), Time.deltaTime * 40f);
        }
        else
        {
            currentSpeed = walkSpeed;
        }

        if (IsGrounded())
        {
            has_jumped = false;

            if (Input.GetKeyDown(KeyCode.Space))
            {
                rb.AddForce(Vector3.up * jumpAmount, ForceMode.Impulse);
                has_jumped = true;
            }
        }

        rb.MovePosition(transform.position + input * Time.deltaTime * currentSpeed);

        UpdateAnimationState();
        SetAnimation(animationState);
    }

    void UpdateAnimationState()
    {
        if (IsGrounded())
        {
            if (currentSpeed >= sprintSpeed)
            {
                animationState = AnimationState.Sprint;
            }
            else if (currentSpeed > runSpeed)
            {
                animationState = AnimationState.Run;
            }
            else if (currentSpeed > walkSpeed)
            {
                animationState = AnimationState.Walk;
            }
            else
            {
                animationState = AnimationState.Idle;
            }
        }
        else
        {
            animationState = has_jumped ? AnimationState.Fall : AnimationState.Jump;
        }
    }

    void SetAnimation(AnimationState state)
    {
        RuntimeAnimatorController curr_anim = anim_idle;
        switch (state)
        {
            case AnimationState.Fall: curr_anim = anim_jump; break;
            case AnimationState.Idle: curr_anim = anim_idle; break;
            case AnimationState.Jump: curr_anim = anim_fall; break;
            case AnimationState.Run: curr_anim = anim_run; break;
            case AnimationState.Sprint: curr_anim = anim_sprint; break;
            case AnimationState.Strafe: curr_anim = anim_strafe; break;
            case AnimationState.Talk: curr_anim = anim_talk; break;
            case AnimationState.Walk: curr_anim = anim_walk; break;
        }

        animator.runtimeAnimatorController = curr_anim;
    }
}
