using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using MongoDB.Driver;
using MongoDB.Bson;

public class Model_Story
{
    public ObjectId _id { set; get; }
    public string theme { set; get; }
    public List<Model_StoryNode> pre_story { set; get; }
    public List<Model_StoryNode> story { set; get; }
    public List<Model_StoryNode> post_story { set; get; }
    public string requested_by { set; get; }
}

public class Model_StoryNode
{
    public string type { set; get; }
    public string voice { set; get; }
    public string action { set; get; }
    public string text { set; get; }
}

public class MongoViewer : MonoBehaviour
{
    private const string MONGO_URI = "mongodb://localhost:27017";
    private const string MONGO_DATABASE = "ai-galileo";
    private MongoClient client;
    private IMongoDatabase db;

    private List<Model_Story> stories;

    private AudioSource audioSource;

    private int current_story = 0;
    private int current_node = 0;


    void Start()
    {
        client = new MongoClient(MONGO_URI);
        db = client.GetDatabase(MONGO_DATABASE);

        stories = getStories();

        PlayNextClip();
    }

    private void Awake()
    {
        audioSource = gameObject.AddComponent<AudioSource>();
    }

    List<Model_Story> getStories()
    {
        // Retrieve all stories
        return db.GetCollection<Model_Story>("stories").Find(_ => true).ToList();
    }

    void PlayNextClip()
    {
        Model_Story story = stories[current_story];
        Model_StoryNode node = story.pre_story[current_node];

        bool found = false;

        while (!found)
        {
            switch (node.type)
            {
                case "text":
                    found = true;
                    break;
                default:
                    IncementNode();
                    node = story.pre_story[current_node];
                    break;
            }
        }

        switch (node.type)
        {
            case "text":
                Debug.Log(node.text);
                if (node.voice != null)
                {
                    WWW www = GetAudioFromFile(node.voice);
                    StartCoroutine(LoadAndPlay(www));
                }
                break;
        }
    }

    private WWW GetAudioFromFile(string filepath)
    {
        WWW request = new("file://" + filepath);
        return request;
    }

    private void IncementNode()
    {
        current_node += 1;

        // Check if we are at the end of the story
        if (current_node >= stories[current_story].pre_story.Count)
        {
            current_story += 1;
            current_node = 0;
        }

        // Check if we are at the end of the stories
        if (current_story >= stories.Count)
        {
            current_story = 0;
            current_node = 0;
        }
    }

    IEnumerator LoadAndPlay(WWW www)
    {
        yield return www;

        audioSource.clip = www.GetAudioClip();
        audioSource.Play();

        while (GetComponent<AudioSource>().isPlaying)
        {
            yield return null;
        }

        IncementNode();
        PlayNextClip();
    }
}
