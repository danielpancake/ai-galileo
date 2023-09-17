using UnityEngine;

public class StudioCamera : MonoBehaviour
{
    private Vector3 offset;
    [SerializeField] private Transform target;
    [SerializeField] private float smoothTime;
    private Vector3 velocity = Vector3.zero;

    private float angle = 0f;
    private float fieldOfView = 40f;

    private void Awake()
    {
        offset = transform.position - target.position;
    }

    private void LateUpdate()
    {
        // Vector3 targetPosition = target.position + offset;
        // targetPosition.x += Mathf.Sin(angle) * 0.5f;
        // targetPosition.z += Mathf.Cos(angle) * 0.5f;

        // transform.position = Vector3.SmoothDamp(transform.position, targetPosition, ref velocity, smoothTime);

        // Apply zoom
        Camera.main.fieldOfView = fieldOfView - Mathf.Sin(angle) * 5f;

        angle += 0.1f * Time.deltaTime;

        // Look at pushnoy face
        // transform.LookAt(target.position + Vector3.up * 1.2f);
    }
}
