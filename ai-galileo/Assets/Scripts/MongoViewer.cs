using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using MongoDB.Driver;
using MongoDB.Bson;
using TMPro;
using UnityEngine.UI;

public class Model_Story
{
    public ObjectId _id { set; get; }
    public ObjectId suggested_topic_id { set; get; }
    public string theme { set; get; }
    public List<Model_StoryNode> story_intro { set; get; }
    public List<Model_StoryNode> story { set; get; }
    public List<Model_StoryNode> story_outro { set; get; }
    public string requested_by { set; get; }
}

public enum StoryPart
{
    Pre,
    Story,
    Post
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
    private const string MONGO_DATABASE = "ai_galileo";
    private MongoClient client;
    private IMongoDatabase db;

    private List<Model_Story> stories;

    private AudioSource audioSource;

    public GameObject pushnoy;

    private int current_story = 0;
    private StoryPart current_story_part = StoryPart.Pre;
    private int current_node = 0;

    [SerializeField]
    public GameObject textMeshContainer;

    private TextMeshProUGUI textMesh;

    void Start()
    {
        client = new MongoClient(MONGO_URI);
        db = client.GetDatabase(MONGO_DATABASE);

        stories = getStories();

        textMesh = textMeshContainer.GetComponent<TextMeshProUGUI>();

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

    Model_StoryNode getCurrentNode(Model_Story story)
    {
        switch (current_story_part)
        {
            default:
            case StoryPart.Pre:
                return story.story_intro[current_node];
            case StoryPart.Story:
                return story.story[current_node];
            case StoryPart.Post:
                return story.story_outro[current_node];
        }
    }

    void PlayNextClip()
    {
        Model_Story story = stories[current_story];
        Model_StoryNode node = getCurrentNode(story);

        bool next_text_found = false;
        while (!next_text_found)
        {
            switch (node.type)
            {
                case "text":
                    next_text_found = true;
                    break;

                case "action":
                    if (node.action.Contains("прыг"))
                    {
                        pushnoy.GetComponent<Character>().Jump();
                    }

                    IncementNode();
                    node = getCurrentNode(story);
                    break;

                default:
                    IncementNode();
                    node = getCurrentNode(story);

                    // TODO: prevent infinite loop
                    break;
            }
        }

        switch (node.type)
        {
            case "text":
                Debug.Log(node.text);
                textMesh.text = node.text;
                if (node.voice != null)
                {
                    StartCoroutine(LoadAndPlay(node.voice));
                }
                break;
        }
    }

    private void IncementNode()
    {
        current_node += 1;

        // Check if we are at the end of the current story part
        List<Model_StoryNode> current_story_part_list;

        switch (current_story_part)
        {
            default:
            case StoryPart.Pre:
                current_story_part_list = stories[current_story].story_intro;
                break;
            case StoryPart.Story:
                current_story_part_list = stories[current_story].story;
                break;
            case StoryPart.Post:
                current_story_part_list = stories[current_story].story_outro;
                break;
        }


        if (current_node >= current_story_part_list.Count)
        {
            if (current_story_part == StoryPart.Pre)
            {
                current_story_part = StoryPart.Story;
                current_node = 0;
            }
            else if (current_story_part == StoryPart.Story)
            {
                current_story_part = StoryPart.Post;
                current_node = 0;
            }
            else if (current_story_part == StoryPart.Post)
            {
                current_story += 1;
                current_story_part = StoryPart.Pre;
                current_node = 0;
            }
        }

        // Check if we are at the end of the stories
        if (current_story >= stories.Count)
        {
            current_story = 0;
            current_node = 0;
        }
    }

    IEnumerator LoadAndPlay(string filepath)
    {
        WWW www = new("file://" + filepath);
        yield return www;

        while (!www.isDone)
        {
            yield return null;
        }

        audioSource.clip = www.GetAudioClip(false);
        audioSource.Play();

        while (audioSource.isPlaying)
        {
            yield return null;
        }

        IncementNode();
        PlayNextClip();
    }
}
